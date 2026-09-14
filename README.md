# ReVision

A visual feedback agent that sees what it builds.

ReVision recreates a static webpage from a reference screenshot, renders its own HTML/CSS in a real browser, and iteratively repairs visual mismatches.

## Current Status

Phase 0, Phase 1, and Phase 2 are implemented. Phase 3 one-shot repair is available as a standalone step.

## Setup

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

Create a local `.env` file with your OpenAI API key and preferred model:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.6-luna
```

## Phase 0 Usage

Run with the default sample page:

```bash
python main.py
```

This verifies the local browser rendering loop and saves:

```text
output/screenshot.png
```

## Phase 1 Usage

Generate HTML/CSS from a target screenshot, then render the first iteration:

```bash
python main.py --target "examples/Yamibuy.png"
```

Outputs:

```text
output/index.html
output/style.css
output/iterations/iteration_0.html
output/iterations/iteration_0.css
output/iterations/iteration_0.png
```

## Phase 2 Usage

Run visual critique against an existing first iteration:

```bash
python main.py --target "examples/Yamibuy.png" --current output/iterations/iteration_0.png --critique
```

Output:

```text
output/iterations/iteration_0_critique.json
```

You can also generate and critique in one command:

```bash
python main.py --target "examples/Yamibuy.png" --critique
```

## Phase 3 Usage

Apply one focused repair pass from a critique JSON, then render the next iteration:

```bash
python main.py --target "examples/Yamibuy.png" --repair output/iterations/iteration_0_critique.json --iteration 1
```

Outputs:

```text
output/index.html
output/style.css
output/iterations/iteration_1.html
output/iterations/iteration_1.css
output/iterations/iteration_1.png
```
