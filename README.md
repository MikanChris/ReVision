# ReVision

A visual feedback agent that sees what it builds.

ReVision recreates a static webpage from a reference screenshot, renders its own HTML/CSS in a real browser, and iteratively repairs visual mismatches.

## Current Status

Phase 0 is implemented:

```bash
python main.py
```

This renders a local HTML page with Playwright and saves a screenshot to:

```text
output/screenshot.png
```

## Setup

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Phase 0 Usage

Run with the default sample page:

```bash
python main.py
```

This phase only verifies the local browser rendering loop. The PNG files in `examples/` are target screenshots for the next phase.

For Phase 1, the expected input will be:

```text
examples/unit convert.png
```

## Phase 1 Usage

Create a local `.env` file with your OpenAI API key:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.6-luna
```

Generate HTML/CSS from a target screenshot, then render the first iteration:

```bash
python main.py --target "examples/unit convert.png"
```

Outputs:

```text
output/index.html
output/style.css
output/iterations/iteration_0.html
output/iterations/iteration_0.css
output/iterations/iteration_0.png
```
