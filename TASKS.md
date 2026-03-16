---
spec_type: TASKS
feature_slug: viral-videos-mvp
status: ready
version: 2.1
loop_mode: ralph
last_updated: 2026-03-15T00:00:00Z
inputs:
* docs/DESIGN_SPEC.md
* docs/specs/README.md
* PROGRESS.md
---

# TASK PLAN - viral-videos-mvp

## LOOP_RULES

* On each iteration, select the first task with `status: false` whose `depends_on` tasks are all `true`.
* Read `docs/DESIGN_SPEC.md` first on every iteration.
* Read `PROGRESS.md` after `docs/DESIGN_SPEC.md` to recover the knowledge produced by previous completed tasks.
* Then read only the files listed under `read_first` for the selected task.
* Complete exactly one task per iteration.
* Run every listed validation check before marking a task complete.
* If any stop condition triggers, stop and update the docs instead of guessing.
* If the task changes business rules, feature scope, contracts, or architecture, update `docs/DESIGN_SPEC.md`.
* If the task changes setup, commands, or operator-facing usage, update `README.md`.
* After a task passes validation, append its outcome to `PROGRESS.md`.
* After a task passes validation, set its `status` to `true`, create one commit for that task, persist the changes, and stop the iteration.

## REVIEW_GATE

* `docs/DESIGN_SPEC.md` and the referenced spec files are internally consistent.
* `PROGRESS.md` reflects the durable knowledge from all completed tasks.
* Task dependencies are acyclic.
* Each task has one clear goal and one bounded scope.
* The next executable task can be selected deterministically.

## TASKS

* id: T-001
  title: Scaffold the minimum repository work tree
  status: true
  type: code
  depends_on: []

* id: T-002
  title: Define the canonical job input schema and validator
  status: true
  type: code
  depends_on: [T-001]

* id: T-003
  title: Implement JobContext path authority
  status: true
  type: code
  depends_on: [T-001]

* id: T-004
  title: Implement asset registry and loaders
  status: true
  type: code
  depends_on: [T-001]

* id: T-005
  title: Implement the Script Writer module
  status: true
  type: code
  depends_on: [T-002, T-003, T-004]

* id: T-006
  title: Implement the TTSProvider adapter interface
  status: true
  type: code
  depends_on: [T-003]

* id: T-007
  title: Implement the TTS module
  status: true
  type: code
  depends_on: [T-006]

* id: T-008
  title: Implement the Timeline Builder module
  status: true
  type: code
  depends_on: [T-007]

* id: T-009
  title: Implement the LipSync adapter interface and static image adapter
  status: true
  type: code
  depends_on: [T-003]

* id: T-010
  title: Implement the LipSync module
  status: true
  type: code
  depends_on: [T-009]

* id: T-011
  title: Implement the Background Selector module
  status: true
  type: code
  depends_on: [T-003, T-004]

* id: T-012
  title: Implement the Subtitle Generator module
  status: true
  type: code
  depends_on: [T-008]

* id: T-013
  title: Implement the FFmpeg adapter
  status: true
  type: code
  depends_on: [T-001]

* id: T-014
  title: Implement the Compositor module
  status: true
  type: code
  depends_on: [T-008, T-010, T-011, T-012, T-013]

* id: T-015
  title: Implement the Pipeline orchestrator
  status: true
  type: code
  depends_on: [T-005, T-007, T-008, T-010, T-011, T-012, T-014]

* id: T-016
  title: Implement the main entry point
  status: true
  type: code
  depends_on: [T-015]

* id: T-017
  title: Add concrete OpenAI LLM adapter
  status: true
  type: code
  depends_on: [T-005]

* id: T-018
  title: Add concrete ElevenLabs TTS adapter
  status: true
  type: code
  depends_on: [T-006]

* id: T-019
  title: Wire providers in pipeline and main; add config files
  status: true
  type: code
  depends_on: [T-017, T-018, T-015]

* id: T-020
  title: Add StaticImageLipSync adapter for MVP lip-sync
  status: true
  type: code
  depends_on: [T-009, T-010]

* id: T-021
  title: Add sequential batch processing and final batch report
  status: true
  type: code
  depends_on: [T-019]

* id: T-022
  title: Harden the MVP with validation, retries, and minimum tests
  status: true
  type: code
  depends_on: [T-020]

* id: T-023
  title: Add minimum operational documentation for humans and agents
  status: true
  type: docs
  depends_on: [T-019]

* id: T-024
  title: Fix silent/quiet audio - diagnose ElevenLabs PCM output and add loudness normalization
  status: true
  type: code
  depends_on: [T-019]
  read_first:
  * docs/DESIGN_SPEC.md
  * app/adapters/elevenlabs_tts_adapter.py
  * app/adapters/ffmpeg_adapter.py
  * app/modules/timeline_builder.py
  * app/modules/tts.py
  goal: >
    Ensure the master audio track and individual TTS segments are audible at
    standard broadcast loudness levels. Currently individual segments peak at
    -20.6 dB and mean at -34.1 dB — far below the expected ~-6 dB peak from
    a well-configured ElevenLabs TTS call.
  scope: >
    app/adapters/elevenlabs_tts_adapter.py,
    app/adapters/ffmpeg_adapter.py,
    app/modules/timeline_builder.py
  instructions: |
    Root-cause the quiet audio before coding a fix:

    1. DIAGNOSE: Check whether the raw PCM bytes returned by the ElevenLabs
       SDK for `output_format="pcm_22050"` are 16-bit signed integers.
       Compute the expected file size (samples × 2 bytes + 44-byte WAV header)
       and compare against the actual file size of a generated segment.
       If the sizes match, the data is being written correctly and the issue
       is low output volume from the API.

    2. DIAGNOSE: Inspect whether `voice_settings` (stability,
       similarity_boost, style, use_speaker_boost) should be added to the
       `text_to_speech.convert()` call to increase output loudness.
       ElevenLabs default stability=0.5, similarity_boost=0.75 can produce
       lower amplitude output; setting use_speaker_boost=True raises loudness.

    3. FIX — normalization step: Add a `normalize_audio` function to
       `app/adapters/ffmpeg_adapter.py` that runs FFmpeg with the
       `loudnorm=I=-14:TP=-1.5:LRA=11` filter to produce a normalized copy
       of the master audio at -14 LUFS (YouTube/streaming standard).

    4. Call `normalize_audio` in `build_timeline` immediately after
       `concat_audio` succeeds, replacing `master_path` in-place so the
       rest of the pipeline picks up the normalized file transparently.

    5. Do NOT change the per-segment WAV files; only the master_audio.wav
       is normalized, preserving original segments for debugging.
  acceptance_criteria:
  * `ffmpeg -af volumedetect` on master_audio.wav reports max_volume >= -3 dB
    after normalization.
  * Individual segment WAV files are unchanged (still raw ElevenLabs output).
  * The final.mp4 audio stream has clearly audible speech when played back.
  * Existing unit tests still pass.
  validation_checks:
  * Run `ffmpeg -i output/jobs/<job>/audio/master/master_audio.wav -af volumedetect -f null /dev/null`
    and confirm max_volume >= -3 dB.
  * Run `pytest` and confirm no regressions.
  stop_conditions:
  * STOP if the ElevenLabs SDK returns a response format other than raw 16-bit
    PCM for `output_format="pcm_22050"` — document the finding and redesign
    the adapter before writing any code.
  rollback_notes:
  * Revert any change that modifies or overwrites individual audio segments.
  * Revert if normalization introduces clipping (TP > 0 dB).

* id: T-025
  title: Fix subtitle font size - subtitles render too large due to libass PlayResY mismatch
  status: true
  type: code
  depends_on: [T-014]
  read_first:
  * docs/DESIGN_SPEC.md
  * app/modules/compositor.py
  * assets/presets/shorts_default.json
  goal: >
    Subtitles in the final.mp4 currently occupy most of the video frame.
    The root cause is that `force_style='FontSize=64'` is passed to the
    FFmpeg `subtitles` filter, but libass uses a default PlayResY=288 when
    rendering SRT files. FontSize=64 at PlayResY=288 scales to
    (64/288)×1920 ≈ 427 px on the 1920-tall canvas — far too large.
  scope: >
    app/modules/compositor.py,
    assets/presets/shorts_default.json
  instructions: |
    Fix the libass font size scaling in the compositor:

    1. In `compose_video`, before building the `force_style` string, compute
       the libass-adjusted font size:

         LIBASS_PLAY_RES_Y = 288  # libass default reference height for SRT
         libass_font_size = max(1, round(sub_style["font_size"] * LIBASS_PLAY_RES_Y / H))

       where H is `preset["height"]` (1920 for shorts_default).
       For the current font_size=64: 64 × 288/1920 = 9.6 → 10 libass pts,
       which renders as visually ≈64 px on a 1920-tall video.

    2. Replace `FontSize={sub_style['font_size']}` with
       `FontSize={libass_font_size}` in the `force_style` string.

    3. Keep `font_size: 64` in `assets/presets/shorts_default.json` as-is —
       it now means "64 visual pixels at the preset's native height", which
       is an intuitive unit.

    4. Add a comment in the compositor near the scaling formula explaining
       the libass PlayResY=288 reference and the scaling rationale.

    5. Do NOT modify the subtitle SRT file or the subtitle generation module.
  acceptance_criteria:
  * Subtitles in final.mp4 are visually approximately 64px tall on the
    1920-pixel-tall canvas (occupying ~3-4% of the vertical space).
  * The `subtitle_safe_area` defined in the preset is respected — subtitles
    appear in the lower portion of the screen, not overlapping character clips.
  * Existing unit tests still pass.
  validation_checks:
  * Render a test job and visually confirm subtitles are readable but not
    oversized (comparable in height to a typical YouTube Shorts subtitle).
  * Run `pytest` and confirm no regressions.
  stop_conditions:
  * STOP if the `subtitles` FFmpeg filter does not accept the `force_style`
    `FontSize` parameter — switch to `drawtext` with explicit coordinate
    calculation instead and document the decision.
  rollback_notes:
  * Revert any change that modifies the SRT content or subtitle timing.
  * Revert if the libass scaling formula changes subtitle positioning
    (x/y) in an unintended way.

* id: T-026
  title: Fix corrupted MP4 output — SAR não-quadrado, áudio 22050Hz mono e bitrate alto
  status: true
  type: code
  depends_on: [T-025]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  * app/modules/compositor.py
  goal: >
    O final.mp4 gerado está inutilizável: VLC exibe tela preta, VS Code reproduce
    sem áudio, e o arquivo é rejeitado pelo WhatsApp e Google Drive.
    Diagnóstico via ffprobe do job job_2026_03_15_935 revelou três causas raiz:
    (1) SAR 10240:10239 em vez de 1:1 — causa tela preta em VLC e rejeição por
    plataformas; (2) áudio 22050 Hz mono — VS Code não reproduz e WhatsApp rejeita;
    (3) bitrate ~4 Mbps gera arquivo de ~17 MB, acima do limite de 16 MB do WhatsApp.
  scope: >
    app/modules/compositor.py
  instructions: |
    Aplicar três correções cirúrgicas em compose_video() em app/modules/compositor.py:

    1. SAR — adicionar setsar=1 nos filtros de escala do filter_complex:
       - Background: alterar `scale={W}:{H}` para `scale={W}:{H},setsar=1`
       - Cada clip ativo: alterar `scale={abox['w']}:{abox['h']}` para
         `scale={abox['w']}:{abox['h']},setsar=1`
       Isso garante SAR 1:1 no output final, eliminando a tela preta no VLC.

    2. Áudio — adicionar os flags de áudio na lista cmd final (antes do path de saída):
         "-ar", "44100",
         "-ac", "2",
       Isso reamostla o áudio de 22050 Hz mono para 44100 Hz estéreo, padrão
       esperado por VS Code, WhatsApp e Google Drive.

    3. Bitrate / tamanho — adicionar flags de codec de vídeo na lista cmd final:
         "-preset", "fast",
         "-crf", "28",
       Isso reduz o bitrate de ~4 Mbps para ~1.5–2 Mbps, mantendo qualidade
       aceitável e produzindo arquivos bem abaixo de 16 MB para vídeos de ~35s.

    NÃO alterar o filter_complex além dos setsar=1.
    NÃO alterar nenhum outro módulo.
    NÃO alterar testes existentes além do necessário para refletir os novos flags.
  acceptance_criteria:
  * `ffprobe final.mp4` mostra SAR 1:1 (sample_aspect_ratio = "1:1").
  * `ffprobe final.mp4` mostra stream de áudio com sample_rate=44100, channels=2.
  * Arquivo final.mp4 tem menos de 16 MB para um job de ~35 segundos.
  * VLC reproduz o vídeo com imagem e áudio sem tela preta.
  * `pytest tests/ -q` passa sem regressões.
  validation_checks:
  * Rodar `ffprobe -v quiet -print_format json -show_streams render/final.mp4`
    e confirmar SAR 1:1, audio sample_rate=44100, channels=2.
  * Confirmar tamanho do arquivo final com `ls -lh render/final.mp4`.
  * Rodar `pytest tests/ -q` e confirmar que todos os testes passam.
  stop_conditions:
  * STOP se os testes de integração do compositor falharem por mudança de contrato
    de duração ou resolução — investigar antes de prosseguir.
  rollback_notes:
  * Reverter qualquer mudança que altere o filter_complex além dos setsar=1.
  * Reverter se a tolerância de duração (0.10s) for violada pelo novo CRF.

* id: T-027
  title: Implementar modo --resume para retomar jobs a partir de artefatos existentes
  status: true
  type: code
  depends_on: [T-026]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/SYSTEM_PIPELINE_ORCHESTRATION_SPEC.md
  * app/pipeline.py
  * app/main.py
  * app/services/file_service.py
  * app/core/job_context.py
  * app/core/contracts.py
  goal: >
    Permitir reexecutar um job já existente (ex: output/jobs/job_2026_03_15_935)
    a partir dos artefatos intermediários já gerados, pulando as etapas cujos
    outputs canônicos já existem em disco e reexecutando apenas as etapas
    seguintes ou as que falharam. Objetivo: evitar reprocessamento caro (LLM,
    TTS, lip-sync) quando apenas o compositor ou os subtítulos precisam ser
    regerados.
  scope: >
    app/services/file_service.py,
    app/pipeline.py,
    app/main.py
  instructions: |
    Implementar o modo de resume em três passos:

    1. PERSISTIR JOB INPUT em init_workspace():
       Em app/services/file_service.py, após criar os subdirs canônicos, serializar
       o ValidatedJob para JSON e escrever em output/jobs/<job_id>/job_input.json.
       Usar ctx.root() / "job_input.json" como path.
       Formato: ctx.job.model_dump() serializado com json.dumps(indent=2).
       Idempotente — sobrescrever sempre que init_workspace é chamado.

    2. ADICIONAR resume_pipeline() em app/pipeline.py:
       Função com assinatura:
         def resume_pipeline(
             job_id: str,
             llm_provider: ScriptGenerator,
             tts_provider: TTSProvider,
             lipsync_engine: LipSyncEngine,
         ) -> JobContext:

       Passos internos de resume_pipeline():
       a. Ler output/jobs/<job_id>/job_input.json e reconstruir ValidatedJob
          via ValidatedJob.model_validate(json.loads(...)).
       b. Criar JobContext(job=validated_job).
       c. Garantir que o workspace existe via init_workspace(ctx) (idempotente).
       d. Para cada stage de 3 a 10, antes de executar, verificar se o artefato
          canônico de saída da stage já existe em disco:
          - write_script     → ctx.script_json() e ctx.dialogue_json()
          - generate_tts     → ctx.audio_manifest()
          - build_timeline   → ctx.timeline_json() e ctx.master_audio()
          - generate_lipsync → todos os clip_file em timeline.json (lê o JSON e
                               verifica se cada Path(item["clip_file"]).exists())
          - prepare_background → ctx.prepared_background()
          - generate_subtitles → ctx.subtitles_srt()
          - compose_video    → ctx.final_mp4()
          Se todos os artefatos de saída de uma stage já existem → logar "skipped"
          e não chamar a função da stage.
          Se qualquer artefato de saída estiver ausente → executar a stage normalmente.
       e. finalize_job: sempre executar (registrar conclusão no log).
       f. Usar o mesmo helper _run/_run_with_retry e o mesmo JobLogger de run_pipeline().
          Logar um evento "stage_skipped" (message="Skipped {stage} — artifacts present")
          para stages puladas (não usar stage_started/stage_completed para stages puladas).

    3. ADICIONAR --resume em app/main.py:
       - Adicionar ao mutually_exclusive_group: `--resume <JOB_ID>`
       - No branch `if args.resume:`, chamar resume_pipeline(args.resume, llm, tts, lipsync).
       - Tratar PipelineError com sys.exit(1), igual ao branch --input.

    Restrições:
    - NÃO modificar run_pipeline() existente — resume_pipeline() é uma função nova.
    - NÃO remover artefatos existentes ao retomar.
    - NÃO reprocessar stages cujos artefatos já existem.
    - job_input.json é o único arquivo novo no workspace; não adicionar outros.

  acceptance_criteria:
  * `python -m app.main --resume job_2026_03_15_935` conclui sem erro usando
    os artefatos já existentes e regenera apenas render/final.mp4 (deletar antes
    para testar).
  * Stages com artefatos presentes emitem evento "stage_skipped" no job.log.
  * Stages sem artefatos executam normalmente e produzem os artefatos esperados.
  * `pytest tests/ -q` passa sem regressões.
  validation_checks:
  * Deletar render/final.mp4 do job existente, rodar --resume e confirmar que
    apenas compose_video é executado (demais stages logam stage_skipped).
  * Confirmar que job.log contém stage_skipped para as stages puladas.
  * Rodar `pytest tests/ -q` e confirmar que todos os testes passam.
  stop_conditions:
  * STOP se job_input.json não existir no job alvo — documentar e orientar
    o usuário a usar --input com o JSON original em vez de --resume.
  * STOP se a reconstrução do ValidatedJob falhar por campos inválidos ou
    ausentes — investigar se o schema mudou desde que o job foi criado.
  rollback_notes:
  * Reverter qualquer mudança em run_pipeline() — apenas resume_pipeline() é nova.
  * Reverter se testes de pipeline ou observabilidade existentes quebrem.

## GLOBAL_CHECKS

* Confirm all touched tests pass before marking any task complete.
* Confirm task dependencies remain acyclic after every edit to this file.
* Confirm no task introduces scope outside `docs/DESIGN_SPEC.md` and the referenced files in `docs/specs/`.
* Confirm `PROGRESS.md` was updated with the result of the completed task.
* Confirm the completed task was recorded in its own commit.
* Confirm the next loop iteration can choose the next task without reading unrelated files.
