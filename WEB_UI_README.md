# Engineering Tools Web Platform

This project now uses a modular Flask structure so you can add new tools without rewriting the existing app.

## Current URL structure

- `/` -> Tool library homepage
- `/tools/un-thread-calculator` -> UN Thread Calculator tool
- `/api/tools/un-thread-calculator/calculate` -> UN tool calculation API

## Project structure

```text
app.py
static/
  site.css                    # shared site styles
templates/
  base.html                   # shared layout shell
  home.html                   # tool library page
tools/
  __init__.py                 # tool registry and metadata
  un_thread/
    calculations.py           # tool-specific math/validation
    routes.py                 # tool-specific pages + API
    templates/un_thread/
      index.html              # tool UI
    static/un_thread/
      style.css               # tool-only CSS
      script.js               # tool-only frontend logic
```

## How to add a new tool

1. Create a folder in `tools/<your_tool>/`.
2. Add `routes.py` with a Flask `Blueprint` and your page/API routes.
3. Add any tool logic in a separate module (for example `calculations.py`).
4. Add templates and static assets inside the tool folder.
5. Register the tool in `tools/__init__.py` by adding a `ToolDefinition` entry.

Example registry entry:

```python
ToolDefinition(
    slug="bolt-torque-calculator",
    name="Bolt Torque Calculator",
    description="Compute tightening torque from diameter, class, and lubricant.",
    category="Fasteners",
    blueprint_import="tools.bolt_torque.routes:bp",
)
```

Once added, it appears automatically on the homepage and its blueprint is auto-registered at startup.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.
