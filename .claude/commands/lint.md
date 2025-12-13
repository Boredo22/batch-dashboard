Run code quality checks on the codebase.

## Python (if ruff/flake8 installed)
```bash
cd c:\Users\bored\batch-dashboard
python -m ruff check . --ignore=E501 || python -m flake8 . --max-line-length=120 --exclude=.venv
```

## Type Checking (if mypy installed)
```bash
python -m mypy app.py main.py job_manager.py --ignore-missing-imports
```

## Frontend (Svelte)
```bash
cd c:\Users\bored\batch-dashboard\frontend
npm run check 2>/dev/null || echo "No svelte-check configured"
```