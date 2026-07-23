# file-server

A single-file Flask server that shares a local directory over HTTP with a
Bauhaus-styled file browser: drag-and-drop upload, in-browser preview,
folder navigation, type filtering, and substring search.

## Install

```bash
pip install flask click
```

## Usage

```bash
# Share the current directory on the default port (32198)
python main.py

# Share a specific directory
python main.py /path/to/folder

# Custom port + debug mode
python main.py . --port 8080 --debug
```

Open the printed URL (`http://<host>:<port>/`) in a browser. Any device on
the same LAN can reach it.

### CLI flags

| Flag | Default | Purpose |
| --- | --- | --- |
| `dir` (positional) | current working dir | directory to share |
| `--port` | `32198` | HTTP port |
| `--debug` | off | Flask debug mode |

## Features

- **Upload** — drag-and-drop or click; progress bar; 100 MB cap.
- **Preview** — PDF, Markdown, HTML, plain text (`.txt/.json/.xml/.csv/...`),
  images (`.png/.jpg/.gif/.svg/...`).
- **Navigation** — breadcrumbs, type filter tabs, substring search.
- **Type encoding** — folder / image / document / code / media / archive,
  each rendered as a Bauhaus shape + color pair.

## Project layout

```
file-server/
├── main.py              # Flask app + card generators + CLI
└── assets/
    ├── index.html       # inline CSS/JS Bauhaus template
    └── favicon_32.png
```

## Tech

Flask · Click · vanilla HTML/CSS/JS (no build step).

## License

MIT
