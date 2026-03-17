# CLAUDE.md

## Modes of operation

**Default mode — answer questions directly.**
If the user asks a question or requests a code change, respond directly.
Do NOT open TASKS.md, PROGRESS.md, or any spec file unless the user explicitly
asks you to run the Ralph Loop or execute a task.

**Ralph Loop mode — only when the user says so.**
Triggered by explicit instructions such as: "run the loop", "execute next task",
"work on TASKS.md", or equivalent.
In this mode, follow the Task loop contract below.

---

## Reading docs — lazy by default

Only open files you actually need for the current request.

| Situation | Files to open |
|---|---|
| General question about the project | Answer from context. No files needed. |
| Implementing a task | `TASKS.md` → `PROGRESS.md` → `docs/DESIGN_SPEC.md` (lookup table only) → the specific spec files listed for that task |
| Debugging a module | Only the spec for that module |
| Changing a contract | The affected spec file + `docs/DESIGN_SPEC.md` §7 |

Never open `docs/PROJECT_*.md` unless a task explicitly requires it.
Never open all spec files at once.

---

## Task loop contract (Ralph Loop mode only)

1. Open `TASKS.md` → pick first task with `status: false` and satisfied dependencies.
2. Open `PROGRESS.md` → recover prior decisions.
3. Open `docs/DESIGN_SPEC.md` → use the lookup table (§8) to identify needed specs.
4. Open **only** the spec files listed under `read_first` for the selected task.
5. Implement exactly one task.
6. Run: `docker compose run --rm app pytest tests/ -q`
7. If tests pass: set `status: true` in `TASKS.md`, append to `PROGRESS.md`, create one commit.
8. Stop.

If step 6 fails: fix code and re-run. Do not advance to step 7.
If docs contradict each other: fix docs before writing code.

---

## Hard rules

- Path assembly → always use `JobContext`, never string concatenation.
- FFmpeg/FFprobe → always via `app/adapters/ffmpeg_adapter.py` and `app/utils/ffprobe_utils.py`.
- External providers → always behind an ABC in `app/adapters/`.
- Credentials → only in `.env`, never in code or Docker image.
- `assets/` → read-only at runtime.
- Exceptions → one per module, at the top of the file.
- One task per commit.
- Never mark a task complete before tests pass.

---

## Key files

| File | When to open |
|---|---|
| `TASKS.md` | Ralph Loop only |
| `PROGRESS.md` | Ralph Loop only |
| `docs/DESIGN_SPEC.md` | When implementing a task — lookup table only |
| `docs/specs/*.md` | Only the file(s) relevant to the current task |
| `config/voices.json` | TTS / character changes |
| `assets/presets/shorts_default.json` | Compositor / layout changes |

---

## Commands reference
```bash
docker compose run --rm app python -m app.main --input inputs/examples/job_001.json
docker compose run --rm app python -m app.main --batch inputs/batch/jobs.csv
docker compose run --rm app pytest
docker compose run --rm app ruff check app/
```