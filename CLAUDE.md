# slide-forge

Self-hosted presentation editor with PPTX export. No Microsoft, no Google, no Electron.

## Quick Start

```bash
pip install -e ".[dev]"
python -m slideforge.tools.generate_template
uvicorn slideforge.server:app --reload --port 8000
# Open http://localhost:8000
```

## Run Tests

```bash
pytest tests/ -v
```

## Conventions

- Python 3.11+, Pydantic v2 models
- ruff for linting (line-length 120)
- Tests use pytest with tmp_path fixtures
- Frontend: vanilla JS, no build step, no npm
- Template layouts use SP_* naming (SP_Title, SP_Content, SP_Intro, SP_Closing, SP_Sources, SP_SectionBreak, SP_Code)
- All styling comes from the template — renderer only writes text content
