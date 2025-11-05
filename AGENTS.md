# AGENTS.md - Jarvis AI Assistant

## Build/Lint/Test Commands
- **Install deps**: `pip install -r requirements.txt`
- **Build executable**: `python build_exe.py`
- **Run tests**: `python -m pytest -v`
- **Run single test**: `python -m pytest path/to/test.py::TestClass::test_method -v`
- **End-to-end test**: `python test_end_to_end.py`
- **Lint**: `ruff check . && ruff format --check .`
- **Format**: `ruff format .`
- **Watch tests**: `watchmedo shell-command --patterns="*.py" --recursive --command="pytest -xvs" .`

## Code Style Guidelines
- **Python version**: 3.10+
- **Line length**: 100 characters
- **Imports**: stdlib → third-party → local, one per line
- **Naming**: PascalCase classes, snake_case functions/variables, UPPER_CASE constants
- **Docstrings**: Triple quotes with description
- **Error handling**: Use try/except with specific exceptions, log with logging module
- **Async**: Use async/await for I/O operations
- **Comments**: Descriptive headers with box drawing chars, # for inline comments
- **Type hints**: Use when clarity benefits outweigh verbosity
- **Linting**: Ruff with E/F/I/W/C90 rules (ignores E501/E722/C901/E402)</content>
<parameter name="filePath">C:\Users\h0093\Documents\jarvis-ai-assistant-v2\AGENTS.md