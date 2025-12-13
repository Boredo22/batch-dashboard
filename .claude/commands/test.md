Run the Python backend tests with coverage report.

```bash
cd c:\Users\bored\batch-dashboard
python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-omit=".venv/*,tests/*"
```

If tests directory doesn't exist yet, create it first and run a simple validation:
```bash
python -c "from config import *; print('Config OK'); from app import app; print('App OK')"
```