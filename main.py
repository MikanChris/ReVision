from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from revision.images import get_image_size
from revision.model import DEFAULT_MODEL, GeneratedCode, OpenAIModel
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
    parser = argparse.ArgumentParser(description="Generate, render, critique, or repair a ReVision page.")
    parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help="Path to a PNG/JPG webpage screenshot. Also used to infer viewport size when --viewport is omitted.",
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
        help="Path where the screenshot should be saved. Defaults depend on the selected phase.",
    )
    parser.add_argument(
        "--viewport",
        type=parse_viewport,
        default=None,
        help=f"Browser viewport as WIDTHxHEIGHT. Defaults to the target image size, or {DEFAULT_VIEWPORT} without --target.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"OpenAI model override for this run. Defaults to OPENAI_MODEL or {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--critique",
        action="store_true",
        help="Run Phase 2 visual critique. With --current, critiques existing screenshots; with --target only, critiques after generation.",
    )
    parser.add_argument(
        "--current",
        type=Path,
        default=None,
        help="Existing rendered screenshot to compare against --target. Defaults to output/iterations/iteration_0.png for --critique.",
    )
    parser.add_argument(
        "--repair",
        type=Path,
        default=None,
        help="Path to a critique JSON file. Runs Phase 3 one-shot repair using current output/index.html and output/style.css.",
    )
    parser.add_argument(
        "--iteration",
        type=int,
        default=1,
        help="Iteration number to save for --repair output. Defaults to 1.",
    )
    return parser


def main() -> None:
    load_dotenv()
    args = build_parser().parse_args()

    workspace = Workspace(Path.cwd())
    viewport = resolve_viewport(args.target, args.viewport)
    renderer = BrowserRenderer(viewport=viewport)

    if args.repair is not None:
        html_path, screenshot_path = repair_iteration(
            critique_path=args.repair,
            iteration=args.iteration,
            workspace=workspace,
            renderer=renderer,
            model_name=args.model,
            output_path=args.output,
        )
        print(f"Viewport: {viewport[0]}x{viewport[1]}")
        print(f"Repaired: {html_path}")
        print(f"Screenshot: {screenshot_path}")
        return

    if args.critique and args.target is None:
        raise RuntimeError("--critique requires --target so the critic can compare against the reference screenshot.")

    if args.critique and args.current is not None:
        critique_path = critique_iteration(
            target_path=args.target,
            current_path=args.current,
            code=workspace.read_generated_code(),
            workspace=workspace,
            model_name=args.model,
        )
        print(f"Viewport: {viewport[0]}x{viewport[1]}")
        print(f"Critique: {critique_path}")
        return

    if args.target is not None:
        html_path, screenshot_path = generate_initial_iteration(
            target_path=args.target,
            workspace=workspace,
            renderer=renderer,
            model_name=args.model,
            output_path=args.output,
        )

        print(f"Viewport: {viewport[0]}x{viewport[1]}")
        print(f"Rendered: {html_path}")
        print(f"Screenshot: {screenshot_path}")

        if args.critique:
            critique_path = critique_iteration(
                target_path=args.target,
                current_path=screenshot_path,
                code=workspace.read_generated_code(),
                workspace=workspace,
                model_name=args.model,
            )
            print(f"Critique: {critique_path}")
        return

    html_path = args.html or workspace.ensure_sample_page()
    screenshot_path = renderer.capture(
        html_path=html_path,
        output_path=args.output or workspace.output_dir / "screenshot.png",
    )

    print(f"Viewport: {viewport[0]}x{viewport[1]}")
    print(f"Rendered: {html_path}")
    print(f"Screenshot: {screenshot_path}")


def resolve_viewport(target_path: Path | None, viewport: tuple[int, int] | None) -> tuple[int, int]:
    if viewport is not None:
        return viewport

    if target_path is not None:
        return get_image_size(target_path)

    return parse_viewport(DEFAULT_VIEWPORT)


def generate_initial_iteration(
    target_path: Path,
    workspace: Workspace,
    renderer: BrowserRenderer,
    model_name: str | None,
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


def critique_iteration(
    target_path: Path,
    current_path: Path,
    code: GeneratedCode,
    workspace: Workspace,
    model_name: str | None,
) -> Path:
    model = OpenAIModel(model=model_name)
    critique = model.critique(target_image_path=target_path, current_image_path=current_path, code=code)
    return workspace.save_critique(iteration=0, critique=critique)


def repair_iteration(
    critique_path: Path,
    iteration: int,
    workspace: Workspace,
    renderer: BrowserRenderer,
    model_name: str | None,
    output_path: Path | None,
) -> tuple[Path, Path]:
    if iteration < 1:
        raise RuntimeError("--iteration must be 1 or greater for repair output.")

    code = workspace.read_generated_code()
    critique = workspace.read_critique(critique_path)

    model = OpenAIModel(model=model_name)
    repaired_code = model.repair(code=code, critique=critique)

    html_path = workspace.write_generated_code(repaired_code)
    workspace.save_iteration_code(iteration=iteration, code=repaired_code)

    screenshot_path = renderer.capture(
        html_path=html_path,
        output_path=output_path or workspace.iterations_dir / f"iteration_{iteration}.png",
    )

    return html_path, screenshot_path


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
