# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a single-file Flask microservice that takes a base image (typically an AI-generated image, e.g. from DALL-E) and overlays text/graphics on it to produce Instagram carousel slides. It's designed to be called by an external automation (e.g. an n8n/Make workflow) that supplies image URLs and a JSON layout spec, and returns a rendered PNG.

All application logic lives in `image_processor.py` — there is no package structure, framework scaffolding, or test suite.

## Running locally

```bash
pip install -r requirements.txt
python image_processor.py        # runs Flask dev server on 0.0.0.0:5000
```

Production runs via gunicorn (as used in the Dockerfile):

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 image_processor:app
```

## Docker

```bash
docker build -t image-processor .
docker run -p 5000:5000 image-processor
```

The Dockerfile downloads font files (Montserrat, Inter) from GitHub at build time into `/app/fonts`. If those downloads fail, the build falls back silently (`fallback.txt`) and `get_font()` at runtime falls back to `ImageFont.load_default()` — keep this in mind when debugging text rendering that looks wrong (wrong font ≠ crash).

There is no test suite, linter, or CI config in this repo. There is no `docker-compose.yml` despite the README referencing one.

## Architecture

Everything is in `image_processor.py`. The important structure:

- **Directories** (created at import time): `./fonts`, `./assets`, `./output`, `./temp`. `./assets/logo.png` is the expected brand logo used for watermarking; `./output` is where generated slides are written and served from.
- **Font resolution** (`get_font`): a small hardcoded map (`Montserrat` → Montserrat-Bold, everything else → Inter-Regular) — adding a font means editing the `FONTS` dict and `fonte_map` together.
- **Text wrapping** (`draw_text_with_wrap`): manual word-wrap using `draw.textbbox` to measure width; used for subtitle/description blocks.

### Request/response contract

- `POST /process-slide` is the core endpoint. It expects a JSON body shaped roughly like:
  - `id` — used to name the output file (`{id}_final.png`)
  - `imagem_dalle_path` or `dalle_image_url` — the source image, either an HTTP(S) URL (downloaded via `requests`) or a local path
  - `camada_texto` — the text/overlay layer, optionally containing (in draw order): `overlay` (semi-transparent black rectangle for legibility), `titulo` (title, supports `\n` or `quebra_linha` for manual line breaks), `elementos_graficos` (list of `linha_decorativa` or `badge` shapes), `subtitulo`, `descricao` (both word-wrapped), `bullet_points` (list of icon+text rows, colored `#0066FF` if `destaque` else `#666666`)
  - `camada_marca` — the branding layer: `logo` (resized/pasted from `assets/logo.png`, positioned bottom-left unless `posicao` contains `"right"`) and `handle` (@handle text, right-aligned if `posicao` contains `"right"`)
  - Field/value strings mix Portuguese keys (`titulo`, `cor`, `tamanho`, `posicao`) with pixel-suffixed values (e.g. `"32px"`, `"#0066FF"`) that get parsed with `.replace('px', '')` / `hex_to_rgb`. Keep this parsing convention if extending the schema — it is not JSON schema-validated, so malformed input mostly surfaces as a 500 with a full traceback in the JSON response.
- Processing order matters: overlay → titulo → elementos_graficos → subtitulo → descricao → bullet_points → logo → handle. Later draws paint over earlier ones.
- Response includes `download_url: /download/<filename>`; `GET /download/<filename>` serves the file straight from `OUTPUT_DIR` with no filename sanitization beyond `os.path.exists` — be careful about path traversal if touching this endpoint.
- `GET /` and `GET /health` are simple status/info endpoints.

### Error handling pattern

`process_slide` wraps the whole pipeline in one try/except and returns `{status: 'erro', erro, stack, timestamp}` with HTTP 500 on any failure, including the full Python traceback. This is intentional for debugging the external caller but means errors are not distinguished by type (e.g. bad input vs. download failure vs. render failure) — if you need finer-grained error responses, add explicit checks (e.g. for missing `dalle_url`) before the broad except.

### Language convention

Code identifiers, log messages, and the JSON payload schema (`camada_texto`, `titulo`, `cor`, etc.) are in Portuguese; keep new fields/log messages consistent with this rather than mixing in English.
