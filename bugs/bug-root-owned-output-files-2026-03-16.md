# Bug Report: Output Files Owned by Root — Inaccessible to Host GUI Apps

**ID:** BUG-002
**Date:** 2026-03-16
**Severity:** Critical
**Status:** Resolved
**Affected Module:** `docker-compose.yml`, `app/adapters/elevenlabs_tts_adapter.py`
**Affected Artifacts:** All files under `output/jobs/<job_id>/`

---

## Summary

All pipeline output files (audio segments, master audio, clips, final MP4) were created with `root:root` ownership because the Docker container runs as root by default. Although the files were technically valid, Snap-confined desktop applications (mpv, VLC) refused to open them, making the output appear "corrupted" to the user.

A secondary bug was also found: `mkdir()` was called after `open()` in the TTS adapter, which would fail on a fresh job if `init_workspace` had not already created the directory.

---

## Symptoms Observed

| Context | Symptom |
|---|---|
| `ffplay` (CLI) | Audio plays correctly |
| `ffprobe` | Reports valid MP3 / WAV / MP4 structure |
| `file` command | Correctly identifies ID3v2.4.0, MPEG ADTS, WAVE PCM |
| mpv (Snap, GUI) | Exit code 2, no output, file appears broken |
| VLC (Snap, GUI) | Cannot open file |
| File manager (Nautilus) | Double-click fails to play |

The files were bitwise identical to working files generated outside Docker. The only difference was ownership.

---

## Root Causes

### 1. Docker Container Runs as Root — Output Files Owned by `root:root`

**Cause:** `docker-compose.yml` had no `user:` directive. The Docker container process ran as UID 0 (root). All files written to the bind-mounted `./output` volume were created with `root:root` ownership on the host.

**Effect:** Snap-confined applications enforce filesystem access policies that prevent reading files owned by a different user (even if POSIX permissions allow it). When the user clicked an output file in their file manager, the Snap-confined mpv/VLC exited silently with error code 2.

**Evidence:**

```
# Pipeline output (broken in GUI):
-rw-r--r-- 1 root   root   26454  001_char_a.mp3

# Test script output (works in GUI):
-rw-rw-r-- 1 oendel oendel 24469  test_tts.mp3
```

Copying the root-owned file to `~/test_audio.mp3` (which changed ownership to the current user) made it playable in mpv immediately.

**Fix:** Added `user: "${UID}:${GID}"` to `docker-compose.yml`. The container now runs as the host user, and all output files inherit the correct ownership.

---

### 2. `mkdir()` Called After `open()` in TTS Adapter

**Cause:** In `app/adapters/elevenlabs_tts_adapter.py`, the directory creation call (`output_path.parent.mkdir(parents=True, exist_ok=True)`) was placed **after** the `with open(output_path, "wb")` block. On a fresh job, `audio/segments/` would not exist yet.

**Effect:** In the pipeline this was masked because `init_workspace()` pre-creates all canonical directories. However, any standalone usage of `ElevenLabsTTSProvider.synthesize()` with a non-existent parent directory would raise `FileNotFoundError`, caught by the broad `except Exception` and re-raised as `TTSError`.

**Fix:** Moved `output_path.parent.mkdir(parents=True, exist_ok=True)` to **before** the `open()` call.

---

## Files Changed

| File | Change |
|---|---|
| `docker-compose.yml` | Added `user: "${UID}:${GID}"` |
| `app/adapters/elevenlabs_tts_adapter.py` | Moved `mkdir()` before `open()`, removed debug print |

---

## Validation

- `file`, `ffprobe`, and `ffplay` confirm all output files are structurally valid.
- After the `user:` fix, output files are created with host user ownership.
- Snap-confined mpv and VLC can now open all output files from the GUI.
- Pipeline end-to-end execution produces playable `final.mp4`.

---

## Prevention

- Docker Compose services that write to bind-mounted volumes should always specify `user:` to match the host user.
- Directory creation (`mkdir`) must always precede file creation (`open`) in adapter code, even when the pipeline pre-creates directories — adapters should be self-contained.
- When users report "corrupted" files, verify with `file`/`ffprobe` first, then check ownership and access context (CLI vs GUI, native vs Snap/Flatpak).

---

## References

- Previous related bug: `bugs/bug-corrupted-mp4-output-2026-03-15.md` (T-026)
- Spec: `docs/DESIGN_SPEC.md` — Docker invariants
