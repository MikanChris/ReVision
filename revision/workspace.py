from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from revision.model import Critique, GeneratedCode, critique_from_dict


SAMPLE_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ReVision Sample</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Arial, Helvetica, sans-serif;
      background: #f4f7fb;
      color: #172033;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background:
        linear-gradient(135deg, rgba(34, 105, 168, 0.12), transparent 34%),
        #f4f7fb;
    }

    main {
      width: min(880px, calc(100vw - 64px));
      padding: 44px;
      border: 1px solid #d9e2ec;
      border-radius: 8px;
      background: #ffffff;
      box-shadow: 0 18px 48px rgba(23, 32, 51, 0.12);
    }

    .eyebrow {
      margin: 0 0 12px;
      color: #1f7a68;
      font-size: 14px;
      font-weight: 700;
      text-transform: uppercase;
    }

    h1 {
      margin: 0 0 16px;
      font-size: 48px;
      line-height: 1.05;
    }

    p {
      max-width: 620px;
      margin: 0 0 28px;
      color: #4b5870;
      font-size: 18px;
      line-height: 1.6;
    }

    .placeholder {
      height: 220px;
      border-radius: 8px;
      background:
        linear-gradient(135deg, #dbe7f3, #b8c9d9);
      border: 1px solid #c7d6e3;
    }
  </style>
</head>
<body>
  <main>
    <p class="eyebrow">Phase 0</p>
    <h1>ReVision browser loop</h1>
    <p>This sample page verifies that Playwright can render local HTML and capture a fixed-viewport screenshot.</p>
    <div class="placeholder" aria-label="Placeholder visual block"></div>
  </main>
</body>
</html>
"""


class Workspace:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.workspace_dir = root / "workspace"
        self.output_dir = root / "output"

    def ensure_sample_page(self) -> Path:
        html_path = self.workspace_dir / "index.html"
        if not html_path.exists():
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            html_path.write_text(SAMPLE_HTML, encoding="utf-8")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        return html_path

    @property
    def iterations_dir(self) -> Path:
        return self.output_dir / "iterations"

    @property
    def generated_html_path(self) -> Path:
        return self.output_dir / "index.html"

    @property
    def generated_css_path(self) -> Path:
        return self.output_dir / "style.css"

    def write_generated_code(self, code: GeneratedCode) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generated_html_path.write_text(code.html, encoding="utf-8")
        self.generated_css_path.write_text(code.css, encoding="utf-8")
        return self.generated_html_path

    def save_iteration_code(self, iteration: int, code: GeneratedCode) -> None:
        self.iterations_dir.mkdir(parents=True, exist_ok=True)
        (self.iterations_dir / f"iteration_{iteration}.html").write_text(code.html, encoding="utf-8")
        (self.iterations_dir / f"iteration_{iteration}.css").write_text(code.css, encoding="utf-8")

    def read_generated_code(self) -> GeneratedCode:
        return GeneratedCode(
            html=self.generated_html_path.read_text(encoding="utf-8"),
            css=self.generated_css_path.read_text(encoding="utf-8"),
        )

    def read_critique(self, path: Path) -> Critique:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError(f"Critique JSON must be an object: {path}")
        return critique_from_dict(payload)

    def save_critique(self, iteration: int, critique: Critique) -> Path:
        self.iterations_dir.mkdir(parents=True, exist_ok=True)
        path = self.iterations_dir / f"iteration_{iteration}_critique.json"
        payload: dict[str, Any] = {
            "summary": critique.summary,
            "issues": critique.issues,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
