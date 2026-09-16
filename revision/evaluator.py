from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


@dataclass(frozen=True)
class EvaluationResult:
    iteration: int
    screenshot: str
    similarity: float
    rmse: float


def compare_images(target_path: Path, current_path: Path) -> tuple[float, float]:
    with Image.open(target_path) as target_image:
        target = target_image.convert("RGB")

    with Image.open(current_path) as current_image:
        current = current_image.convert("RGB")

    if current.size != target.size:
        current = current.resize(target.size, Image.Resampling.LANCZOS)

    diff = ImageChops.difference(target, current)
    stat = ImageStat.Stat(diff)
    squared_sum = sum(value ** 2 for value in stat.rms) / len(stat.rms)
    rmse = math.sqrt(squared_sum)
    similarity = max(0.0, 1.0 - (rmse / 255.0))
    return similarity, rmse


def evaluate_iterations(target_path: Path, iterations_dir: Path) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []

    for screenshot_path in sorted(iterations_dir.glob("iteration_*.png")):
        stem_parts = screenshot_path.stem.split("_")
        if len(stem_parts) != 2 or not stem_parts[1].isdigit():
            continue

        iteration = int(stem_parts[1])
        similarity, rmse = compare_images(target_path=target_path, current_path=screenshot_path)
        results.append(
            EvaluationResult(
                iteration=iteration,
                screenshot=str(screenshot_path),
                similarity=similarity,
                rmse=rmse,
            )
        )

    return sorted(results, key=lambda result: result.iteration)
