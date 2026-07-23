# AI Net Shield API

Deterministic readiness scoring for controlled AI Net Shield integrations.

The public WordPress assessment scores answers in the visitor's browser and
does not call this service. The API remains available for explicitly approved
integrations and retains the original `/analyze` endpoint during the transition.

## Endpoints

- `GET /health`
- `POST /analyze` - compatibility endpoint for exactly 10 boolean answers
- `POST /v2/analyze` - current 24-control assessment

The service does not write assessment data to a database or log request bodies.

## Local verification

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest
uvicorn main:app --reload
```

## Configuration

`ALLOWED_ORIGINS` is a comma-separated list. Production defaults to the
canonical AI Net Strategies origins when the variable is omitted.
