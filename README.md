# slide-forge

A self-hosted presentation editor with PPTX export, focused on technical and educational content.

## Features

- Browser-based slide editor (no install needed beyond Python)
- 7 slide layouts: Title, Content, Intro, Closing, Sources, Section Break, Code
- PPTX export using python-pptx with template-based rendering
- JSON storage — no database required
- Vanilla JS frontend — no build step
- Review & approve workflow via FastAPI endpoints

## Getting Started

```bash
pip install -e ".[dev]"
python -m slideforge.tools.generate_template
uvicorn slideforge.server:app --reload --port 8000
```

Then open http://localhost:8000 in your browser.

## Bullet Style / Verbosity

Bullet point verbosity is controlled at **content generation time** by the upstream pipeline (e.g. schulpipeline), not in the web editor. The `PresentationStyle` enum defines three levels:

| Style | Description |
|-------|-------------|
| `keywords` | Single keywords or short phrases (2-3 words), no verbs |
| `sentences` | One complete sentence per bullet (8-15 words) |
| `academic` | Formal language with domain terminology and references |

The style is set on the `Presentation` model when content is generated and stored alongside the slides. The web editor focuses on reordering, editing, and reviewing the content — not regenerating it.

## Integration with schulpipeline

slide-forge is used as the rendering backend for schulpipeline's PPTX output. The integration flow:

1. schulpipeline's **synthesize** stage generates structured content (title, sections, bullet points)
2. The **converter** module (`schulpipeline.artifacts.converter`) transforms synthesis output into a slide-forge `Presentation`
3. The presentation is either rendered directly to PPTX or sent to slide-forge's review server for editing before export

## Project Structure

```
slideforge/
├── models.py            # Pydantic models (Slide, Presentation, PresentationStyle)
├── server.py            # FastAPI app (REST API + static frontend)
├── storage.py           # JSON file-based project store
├── renderer.py          # PPTX rendering via python-pptx
├── template_loader.py   # Template validation and layout lookup
├── prompts.py           # Style instructions for LLM content generation
└── tools/
    └── generate_template.py  # Generate the PPTX template with all layouts
frontend/
├── index.html           # Single-page editor
├── app.js               # Editor logic (vanilla JS)
└── style.css            # Styling
tests/
├── test_models.py       # Model unit tests
├── test_renderer.py     # PPTX rendering tests
├── test_server.py       # API integration tests
├── test_storage.py      # Storage tests
└── test_template.py     # Template loader tests
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/projects` | Create a new project |
| `GET` | `/api/projects/{id}` | Get project details |
| `PUT` | `/api/projects/{id}` | Update a project |
| `DELETE` | `/api/projects/{id}` | Delete a project |
| `GET` | `/api/projects/{id}/export` | Export as PPTX |
| `POST` | `/api/projects/{id}/approve` | Mark as approved |
| `GET` | `/api/projects/{id}/approved` | Check approval status |
| `GET` | `/api/layouts` | List available layouts |

## Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Requirements

- Python 3.11+
- FastAPI, uvicorn, python-pptx, Pydantic v2

## License

MIT
