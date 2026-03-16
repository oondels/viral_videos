---
name: pipeline_audio_video_bugs
description: Known bugs in the audio/video generation pipeline — corrupted MP4 output investigation (2026-03-16)
type: project
---

Bug: MP4 final corrompido — sem áudio no VS Code, tela preta no VLC, erro ao compartilhar.

**Why:** O commit T-026 tentou corrigir SAR, sample rate e bitrate, mas o problema persiste. A investigação de 2026-03-16 identificou múltiplas causas raiz remanescentes.

**How to apply:** Usar os findings SEV-001 a SEV-007 como guia para o próximo ciclo de correção.

Causa raiz primária (Crítico):
- ElevenLabs TTS gera WAV a 22050 Hz mono
- concat_audio usa "-c copy" — não reencode, preserva 22050 Hz
- normalize_audio converte para WAV mas não força sample rate nem canais
- O master_audio.wav resultante pode ser 22050 Hz mono
- O compositor passa -ar 44100 -ac 2 ao FFmpeg FINAL mas o -i do master audio
  já está indexado como o ÚLTIMO input — o resampling só ocorre durante o encode,
  e com concat demuxer + copy stream, o WAV pode ter sample rate inconsistente
  entre segmentos se o provider mudar taxa

Causa raiz secundária (Alto):
- StaticImageLipSync gera clips com áudio embutido (aac 192k)
  mas o spec diz "not embed an authoritative audio track"
- O clip tem dimensões variáveis (não forçadas para abox['w'] x abox['h'] antes)
  dependendo da imagem de entrada (base.png pode ter qualquer tamanho)
- setsar=1 adicionado no T-026 apenas no scale do clip no filter_complex,
  mas o prepared_background.mp4 não tem setsar=1 na escala

Causa raiz terciária (Médio):
- scale_and_trim_video não adiciona setsar=1 — o prepared_background.mp4
  pode sair com SAR não unitário se o source tiver SAR estranho
- moov atom: não há -movflags +faststart no comando final — dificulta
  streaming/compartilhamento progressivo
