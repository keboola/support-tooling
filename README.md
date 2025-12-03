## App to control Manage API

### Run locally

```bash
uv run streamlit run
```

### Only sync dependencies & create venv

```bash
uv sync  # add -U to upgrade dependencies if you want to
```

### Export requirements.txt based on uv.lock

```bash
uv export -o requirements.txt
```
