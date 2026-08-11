# CI: import boundaries

Add `.github/workflows/import-boundaries.yml` after merge (requires `workflow` scope to push):

```yaml
name: import-boundaries

on:
  push:
    branches: ["**"]
  pull_request:

jobs:
  lint-imports:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install package (dev)
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Unit tests (boundaries + core)
        run: pytest tests/unit -q
      - name: Import linter contracts
        run: lint-imports
```

Local equivalent: `pytest tests/unit -q && lint-imports`
