"""Canonical exception base class for the viral-videos pipeline.

All domain exceptions in this project should be subclasses of ViralVideosError.
Canonical hierarchy:

  ViralVideosError
  ├── PipelineError         (app.pipeline)
  ├── ScriptGenerationError (app.adapters.llm_adapter)
  ├── TTSError              (app.adapters.tts_provider_adapter)
  ├── LipSyncError          (app.adapters.lipsync_engine_adapter)
  ├── FFmpegError           (app.adapters.ffmpeg_adapter)
  ├── AssetError            (app.services.asset_service)
  ├── BackgroundError       (app.modules.background_selector)
  ├── CompositorError       (app.modules.compositor)
  ├── TimelineError         (app.modules.timeline_builder)
  └── SubtitleError         (app.modules.subtitles)
"""


class ViralVideosError(Exception):
    """Base class for all viral-videos domain errors."""
