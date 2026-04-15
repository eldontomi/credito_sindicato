# CCB Portal Backend

Backend API and financial engine for the CCB portal.

## Local development

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn ccb.main:app --reload
```
