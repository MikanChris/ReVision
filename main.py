from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from revision.model import DEFAULT_MODEL, OpenAIModel
from revision.renderer import BrowserRenderer
from revision.workspace import Workspace


DEFAULT_VIEWPORT = "1440x900"


def parse_viewport(value: str) -> tuple[int, int]:
    try:
        width_text, height_text = value.lower().split("x", 1)
        width = int(width_text)
        height = int(height_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Viewport must use WIDTHxHEIGHT, for example 1440x900.") from exc

    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("Viewport width and height must be positive.")

    return width, height


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate or render a ReVision page and capture a screenshot.")
    parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help="Path to a PNG/JPG webpage screenshot. When provided, ReVision generates HTML/CSS from this image.",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=None,
        help="Path to an HTML file to render. Defaults to workspace/index.html when --target is not provided.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path where the screenshot should be saved. Defaults to output/screenshot.png or output/iterations/iteration_0.png.",
    )
    parser.add_argument(
        "--viewport",
        type=parse_viewport,
        default=parse_viewport(DEFAULT_VIEWPORT),
        help=f"Browser viewport as WIDTHxHEIGHT. Defaults to {DEFAULT_VIEWPORT}.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"OpenAI model override for this run. Defaults to OPENAI_MODEL or {DEFAULT_MODEL}.",
    )
    return parser


def main() -> None:
    load_dotenv()
    args = build_parser().parse_args()

    workspace = Workspace(Path.cwd())
    renderer = BrowserRenderer(viewport=args.viewport)

    if args.target is not None:
        html_path, screenshot_path = generate_initial_iteration(
            target_path=args.target,
            workspace=workspace,
            renderer=renderer,
            model_name=args.model,
            output_path=args.output,
        )
    else:
        html_path = args.html or workspace.ensure_sample_page()
        screenshot_path = renderer.capture(
            html_path=html_path,
            output_path=args.output or workspace.output_dir / "screenshot.png",
        )

    print(f"Rendered: {html_path}")
    print(f"Screenshot: {screenshot_path}")


def generate_initial_iteration(
    target_path: Path,
    workspace: Workspace,
    renderer: BrowserRenderer,
    model_name: str,
    output_path: Path | None,
) -> tuple[Path, Path]:
    model = OpenAIModel(model=model_name)
    code = model.generate_page(target_path)

    html_path = workspace.write_generated_code(code)
    workspace.save_iteration_code(iteration=0, code=code)

    screenshot_path = renderer.capture(
        html_path=html_path,
        output_path=output_path or workspace.iterations_dir / "iteration_0.png",
    )

    return html_path, screenshot_path


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
