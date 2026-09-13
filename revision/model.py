from __future__ import annotations

import base64
import json
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from revision.prompts import GENERATE_PAGE_PROMPT


DEFAULT_MODEL = "gpt-5.6-luna"


@dataclass(frozen=True)
class GeneratedCode:
    html: str
    css: str


class ModelResponseError(RuntimeError):
    pass


class OpenAIModel:
    def __init__(self, model: str | None = None) -> None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Create a .env file from .env.example or set the environment variable."
            )

        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
        self.client = OpenAI()

    def generate_page(self, target_image_path: Path) -> GeneratedCode:
        image_url = image_to_data_url(target_image_path)

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": GENERATE_PAGE_PROMPT},
                        {"type": "input_image", "image_url": image_url, "detail": "high"},
                    ],
                }
            ],
        )

        return parse_generated_code(response.output_text)


def image_to_data_url(path: Path) -> str:
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"Target image does not exist: {path}")

    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "image/png"

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def parse_generated_code(text: str) -> GeneratedCode:
    payload = parse_json_object(text)

    html = payload.get("html")
    css = payload.get("css")

    if not isinstance(html, str) or not html.strip():
        raise ModelResponseError("Model response did not include a non-empty html string.")

    if not isinstance(css, str):
        raise ModelResponseError("Model response did not include a css string.")

    return GeneratedCode(html=html.strip(), css=css.strip())


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = strip_code_fence(text.strip())

    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ModelResponseError("Model response was not valid JSON.") from None

        try:
            value = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ModelResponseError(f"Model response JSON could not be parsed: {exc}") from exc

    if not isinstance(value, dict):
        raise ModelResponseError("Model response JSON must be an object.")

    return value


def strip_code_fence(text: str) -> str:
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()

    return text
