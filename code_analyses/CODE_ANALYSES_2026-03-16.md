# Auditoria do Pipeline de Video — 2026-03-16

## Contexto

Sintomas reportados no video final gerado pelo pipeline:
- **VS Code:** video sem audio
- **VLC:** video preto com audio
- **Compartilhamento:** erro ao tentar compartilhar (WhatsApp, Google Drive), como se o arquivo estivesse corrompido

O pipeline executa o roteiro corretamente, gera falas (TTS), cria legendas, porem falha no video final.

---

## Resumo — Findings: 9 (Crit: 2 | High: 3 | Med: 3 | Low: 1)

---

### [SEV-001] Sample rate 22050 Hz propagado ate o master audio sem reencoding garantido

- **Severidade:** Critico
- **Localizacao:** `app/adapters/elevenlabs_tts_adapter.py:54` + `app/adapters/ffmpeg_adapter.py:59-66`
- **Spec:** MODULE_TTS_SPEC — "All persisted segment files must share the same sample rate"
- **Descricao:** O ElevenLabs adapter solicita `output_format="pcm_22050"` e grava o WAV explicitamente com `wf.setframerate(22050)`. O `concat_audio()` usa `-c copy`, copiando streams sem reencoding. Isso preserva os 22050 Hz nos segmentos. A chamada `normalize_audio()` em `timeline_builder.py:57` aplica loudnorm mas **nao forca sample rate nem canais** — o WAV de saida herda a configuracao do input (22050 Hz, mono). O `master_audio.wav` final chega ao compositor com 22050 Hz mono. O compositor aplica `-ar 44100 -ac 2` ao encode final, mas isso e um resampling on-the-fly pelo libavcodec; se o muxer AAC tiver edge cases com esse salto de 2:1, o stream de audio pode ficar out-of-sync ou ser ignorado pelo player.
- **Impacto:** O VLC toca audio (le o stream nativo 22050 Hz do master antes do encode) mas mostra tela preta porque a muxagem esta inconsistente. O VS Code usa o decoder de sistema (QuickTime/Media Foundation) que pode recusar a stream de audio por causa do mismatch de sample rate declarado versus real no moov atom. Qualquer re-muxer (WhatsApp, Google Drive) que inspeciona o moov pode rejeitar o arquivo.
- **Recomendacao:** Em `normalize_audio()`, adicionar `-ar 44100 -ac 2` ao comando FFmpeg para forcar resampling e stereo antes do `loudnorm`. Alternativamente, acrescentar uma etapa explicita de resampling em `build_timeline()` apos `concat_audio()`. O codec resultante do master deve declarar 44100 Hz / stereo antes de entrar no compositor.

---

### [SEV-002] `moov atom` nao posicionado no inicio do arquivo (falta `+faststart`)

- **Severidade:** Critico
- **Localizacao:** `app/modules/compositor.py:227-241`
- **Spec:** MODULE_COMPOSITOR_SPEC — "export one publishable MP4" / "The final audio track matches master_audio.wav"
- **Descricao:** O comando FFmpeg final **nao inclui** `-movflags +faststart`. Sem essa flag, o `moov atom` (indice de todos os streams) e escrito no **fim** do arquivo pelo muxer MP4. Players progressivos (VS Code, WhatsApp, Google Drive preview) precisam do `moov atom` no inicio para iniciar a reproducao sem baixar o arquivo inteiro. Sem ele, o VS Code pode exibir o video "sem audio" porque nao consegue parsear o container corretamente em streaming, e ao tentar compartilhar o arquivo, servicos que fazem leitura sequencial do header falham com erro de container mal formado.
- **Impacto:** Este e provavelmente o principal responsavel pelos tres sintomas reportados simultaneamente: VS Code sem audio, VLC tela preta, erro ao compartilhar. O arquivo nao esta tecnicamente corrompido — o VLC consegue ler porque ele faz seek para o fim para encontrar o `moov` — mas nao e um MP4 "publicavel" conforme a spec.
- **Recomendacao:** Adicionar `-movflags +faststart` ao comando de saida do `compose_video()` em `compositor.py`. A posicao correta e junto com os outros flags de codec, por exemplo: `"-movflags", "+faststart"`.

---

### [SEV-003] `StaticImageLipSync` embute faixa de audio nos clips, violando o contrato do adapter

- **Severidade:** Alto
- **Localizacao:** `app/adapters/static_lipsync_adapter.py:23-36`
- **Spec:** `lipsync_engine_adapter.py` docstring — "not embed an authoritative audio track (the compositor uses master audio)" + MODULE_LIPSYNC_SPEC implicito
- **Descricao:** O `StaticImageLipSync.generate()` passa `-c:a aac -b:a 192k` ao FFmpeg e usa `-shortest` que sincroniza video com o audio embutido. O clip gerado contem uma faixa de audio AAC. No compositor, o mapeamento usa `[clip_in]:v` para extrair apenas o stream de video, entao o audio do clip nao e incluido — mas o clip ter audio embutido aumenta o tamanho do arquivo, pode causar problemas de sincronizacao de PTS entre o stream de video do clip (que foi encodado com referencia ao audio interno) e o master audio externo, e viola explicitamente o contrato da ABC.
- **Impacto:** Potencial dessincronizacao de PTS (presentation timestamp) entre clips e master audio no compositor. O `filter_complex` usa `-itsoffset` para posicionamento temporal — se os PTS do clip forem indexados em relacao ao audio interno do proprio clip, o offset pode nao alinhar corretamente com o master. Alto risco de drift de sincronizacao.
- **Recomendacao:** Remover `-c:a aac -b:a 192k` e substituir `-shortest` por `-t` com a duracao medida do audio. Comando correto: `"-loop", "1", "-i", str(image_path), "-t", str(audio_duration), "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-an"`. A duracao deve ser medida com `get_audio_duration(audio_path)` antes de chamar o FFmpeg.

---

### [SEV-004] `scale_and_trim_video` nao adiciona `setsar=1` no prepared background

- **Severidade:** Alto
- **Localizacao:** `app/adapters/ffmpeg_adapter.py:128-131`
- **Spec:** MODULE_BACKGROUND_SELECTOR_SPEC — "scale-to-cover then crop must be used to avoid letterboxing"
- **Descricao:** O T-026 adicionou `setsar=1` no `filter_complex` do compositor para os **clips** (linha `compositor.py:144` e `compositor.py:176`), mas **nao** adicionou para o background. O `scale_and_trim_video` em `ffmpeg_adapter.py` usa `scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}` sem `setsar=1`. Se o video de background de origem tiver um SAR diferente de 1:1 (comum em videos do YouTube/TikTok baixados), o `prepared_background.mp4` sera entregue ao compositor com SAR nao unitario. O filtro `[{bg_idx}:v]scale={W}:{H},setsar=1[bg_base]` no compositor (linha 144) corrige isso, mas a correcao esta no lugar certo. **No entanto**, se o compositor falhar antes de processar o background, o artefato em disco fica corrompido para reuse.
- **Impacto:** Com o `setsar=1` no compositor presente (linha 144), o impacto direto no video final e mitigado. Mas o `prepared_background.mp4` em disco pode ter SAR incorreto, enganando futuras inspecoes manuais e o modo `--resume` (que pula `prepare_background` se o arquivo existir).
- **Recomendacao:** Adicionar `,setsar=1` ao `scale_filter` em `scale_and_trim_video()`: `f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1"`.

---

### [SEV-005] `concat_audio` usa `-c copy` sem verificar que todos os segmentos tem o mesmo sample rate e canais

- **Severidade:** Alto
- **Localizacao:** `app/adapters/ffmpeg_adapter.py:36-67`
- **Spec:** `ffmpeg_adapter.py:39` — "All inputs must share the same sample rate and channel layout"
- **Descricao:** O comentario da funcao diz "All inputs must share the same sample rate and channel layout" mas o codigo nao verifica isso — confia apenas na afirmacao da spec do TTS. Se o provider ElevenLabs retornar segmentos com taxas diferentes (por ex. em caso de fallback do SDK), o concat demuxer com `-c copy` ira muxar streams incompativeis silenciosamente, produzindo um WAV com timestamps quebrados. Adicionalmente, o WAV resultante sera mono 22050 Hz (o que o ElevenLabs produz), o que diverge do target esperado de 44100 Hz stereo para o output final.
- **Impacto:** Master audio com sample rate incorreto ou timestamps quebrados, causando dessincronizacao no video final.
- **Recomendacao:** Adicionar reencoding explicito em `concat_audio` ou criar uma funcao `concat_and_normalize_audio` que forca `-ar 44100 -ac 2` na saida. Alternativamente, `normalize_audio()` deve sempre forcar `44100 Hz / stereo` independentemente do input. A opcao mais cirurgica: modificar `normalize_audio()` para incluir `-ar 44100 -ac 2` nos argumentos FFmpeg.

---

### [SEV-006] Timeline calculada com `duration_sec` dos segmentos originais (22050 Hz) mas master audio apos loudnorm pode ter duracao ligeiramente diferente

- **Severidade:** Medio
- **Localizacao:** `app/modules/timeline_builder.py:64-92`
- **Spec:** MODULE_TIMELINE_BUILDER_SPEC — "the final end_sec matches the master audio duration within 0.05 seconds"
- **Descricao:** O `build_timeline()` calcula os `start_sec`/`end_sec` usando `duration_sec` do manifesto, que foi medido **antes** da normalizacao. O `master_audio.wav` e entao reescrito pelo `normalize_audio()`. O `loudnorm` de dois passes pode alterar levemente a duracao do arquivo (o filtro loudnorm em modo linear pode adicionar ou remover frames de padding). A validacao `abs(final_end - master_duration) > 0.05` protege contra divergencias grosseiras, mas se a normalizacao alterar a duracao em mais de 50ms, a pipeline levanta `TimelineError`. O risco real e que, se for adicionado resampling de 22050->44100 Hz (correcao do SEV-001), a duracao do master pode mudar mais do que 50ms dependendo de como o FFmpeg lida com os frames de silencio de padding no resampling.
- **Impacto:** Potencial falha em `TimelineError` apos a correcao do SEV-001, ou video com ultimo segundo truncado/estendido.
- **Recomendacao:** Recalcular `master_duration` apos a normalizacao (e apos qualquer futuro resampling) e usar esse valor para a validacao. O cursor de timeline deve continuar sendo calculado a partir dos segmentos originais, mas a validacao final deve comparar com o arquivo masterizado efetivamente gerado.

---

### [SEV-007] `StaticImageLipSync` nao forca `pix_fmt yuv420p` de forma garantida com `-tune stillimage`

- **Severidade:** Medio
- **Localizacao:** `app/adapters/static_lipsync_adapter.py:27-35`
- **Spec:** MODULE_COMPOSITOR_SPEC — "pixel format yuv420p"
- **Descricao:** O comando inclui `-pix_fmt yuv420p`, mas `-tune stillimage` no libx264 pode interagir com `-pix_fmt` de forma inesperada dependendo do formato da imagem de entrada (base.png). Se o base.png for RGBA (canal alpha), o FFmpeg pode recusar ou fazer conversao para YUV com dithering. O compositor aplica `scale={abox['w']}:{abox['h']},setsar=1` mas nao adiciona `format=yuv420p` no filtro de escala do clip — confia que o input ja esta em yuv420p.
- **Impacto:** Se um clip chegar ao compositor em yuv444p ou yuv420p(pc range), o overlay pode produzir artefatos de cor ou o encoder final pode recusar.
- **Recomendacao:** Em `static_lipsync_adapter.py`, garantir conversao explicita da imagem antes do encode: adicionar `-vf "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p"` antes do `-c:v libx264`. Alternativamente, no compositor, adicionar `format=yuv420p` ao filtro de scale de cada clip: `scale={abox['w']}:{abox['h']},setsar=1,format=yuv420p`.

---

### [SEV-008] Dimensoes do clip nao sao forcadas antes de entrar no `filter_complex` — dependencia implicita de tamanho da base.png

- **Severidade:** Medio
- **Localizacao:** `app/adapters/static_lipsync_adapter.py:23-36` + `app/modules/compositor.py:175-176`
- **Spec:** MODULE_COMPOSITOR_SPEC — "Layout geometry must come from the selected render preset"
- **Descricao:** O `StaticImageLipSync` nao recebe informacao sobre o tamanho target do clip (`abox['w'] x abox['h']`). O clip e gerado com as dimensoes da `base.png` de origem (atualmente gerada com Pillow em tamanho arbitrario no T-013). O compositor entao escala o clip via `scale={abox['w']}:{abox['h']}` no `filter_complex`. Isso funciona se a `base.png` tiver proporcao compativel, mas se a imagem tiver dimensoes impares ou proporcao muito diferente, o `scale` forcado sem `force_original_aspect_ratio` pode distorcer o personagem.
- **Impacto:** Distorcao visual do personagem no video final. Risco de dimensoes impares causando erro de encode em libx264 (que exige largura e altura pares para yuv420p).
- **Recomendacao:** No compositor, substituir `scale={abox['w']}:{abox['h']}` por `scale={abox['w']}:{abox['h']}:force_original_aspect_ratio=decrease,pad={abox['w']}:{abox['h']}:(ow-iw)/2:(oh-ih)/2,setsar=1` para manter proporcao e centralizar, ou garantir que `base.png` seja sempre criada com dimensoes exatas correspondentes ao preset.

---

### [SEV-009] `get_audio_duration` usado em `lipsync.py:68` para medir duracao de um arquivo MP4 de video

- **Severidade:** Baixo
- **Localizacao:** `app/modules/lipsync.py:68`
- **Spec:** MODULE_LIPSYNC_SPEC — "duration within 0.10s of the source audio duration"
- **Descricao:** `get_audio_duration(clip_path)` e chamado para medir a duracao do clip MP4 gerado pelo lipsync engine. A funcao delega para `get_media_duration()` que usa `ffprobe -show_entries format=duration` — isso retorna a duracao do container, nao especificamente do stream de video. Para o `StaticImageLipSync` com `-shortest`, a duracao do container e determinada pelo stream de audio embutido, o que pode mascarar um clip de video mais curto (o `-shortest` pode truncar o stream de video antes do final do audio). Semanticamente, chamar `get_audio_duration` num arquivo de video e incorreto e confunde leitores do codigo.
- **Impacto:** Baixo risco funcional com a implementacao atual, mas pode mascarar bugs em implementacoes reais de lipsync onde video e audio tem duracoes diferentes.
- **Recomendacao:** Renomear a chamada para `get_media_duration(clip_path)` (que e o que efetivamente roda). Considerar usar `get_video_dimensions()` + um check de stream de video especifico para validar que o clip tem stream de video valido.

---

## Diagnostico Consolidado — Causa Raiz do Bug Reportado

O comportamento observado (VS Code sem audio, VLC tela preta com audio, erro ao compartilhar) aponta para **dois defeitos primarios atuando em conjunto**:

### 1. Falta de `-movflags +faststart` (SEV-002) — causa provavel da maioria dos sintomas

O `moov atom` no final do arquivo faz com que players que nao suportam seek reverso (VS Code, WhatsApp, Google Drive) nao consigam parsear o container corretamente. O VLC consegue reproduzir porque faz seek ate o final para encontrar o `moov`, mas exibe tela preta porque o stream de video tem problemas de PTS (veja item 2).

### 2. Dessincronizacao de PTS causada por audio 22050 Hz mono no master + clips com audio embutido (SEV-001 + SEV-003)

O master audio chega ao compositor a 22050 Hz mono. O resampling on-the-fly para 44100 Hz stereo durante o encode final pode produzir um stream AAC com PTS desalinhados em relacao ao stream de video. Simultaneamente, os clips do `StaticImageLipSync` tem faixa de audio AAC embutida — seus PTS de video foram calculados em relacao ao audio interno, nao ao master. Quando o compositor descarta o audio do clip e usa `-itsoffset` para posicionamento, os PTS do stream de video do clip podem nao corresponder ao tempo esperado, resultando em frames pretos nos intervalos.

---

## Ordem de Correcao Recomendada

| # | Severidade | Correcao | Arquivo |
|---|-----------|----------|---------|
| 1 | Critico | Adicionar `-movflags +faststart` ao comando FFmpeg final | `compositor.py` |
| 2 | Critico | Forcar `-ar 44100 -ac 2` em `normalize_audio()` | `ffmpeg_adapter.py` |
| 3 | Alto | Remover audio dos clips: usar `-t <duration> -an` em vez de `-shortest` | `static_lipsync_adapter.py` |
| 4 | Alto | Adicionar `setsar=1` em `scale_and_trim_video()` | `ffmpeg_adapter.py` |
| 5 | Alto | Validar sample rate/canais em `concat_audio()` | `ffmpeg_adapter.py` |
| 6 | Medio | Recalcular `master_duration` pos-normalizacao | `timeline_builder.py` |
| 7 | Medio | Forcar `format=yuv420p` nos clips | `static_lipsync_adapter.py` / `compositor.py` |
| 8 | Medio | Forcar dimensoes corretas nos clips | `compositor.py` |
| 9 | Baixo | Renomear `get_audio_duration` para `get_media_duration` no lipsync | `lipsync.py` |
