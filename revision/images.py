from __future__ import annotations

import struct
from pathlib import Path


class ImageSizeError(RuntimeError):
    pass


def get_image_size(path: Path) -> tuple[int, int]:
    path = path.resolve()
    with path.open("rb") as file:
        header = file.read(32)

    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return read_png_size(header)

    if header.startswith(b"\xff\xd8"):
        return read_jpeg_size(path)

    raise ImageSizeError(f"Unsupported image format for viewport detection: {path}")


def read_png_size(header: bytes) -> tuple[int, int]:
    if len(header) < 24:
        raise ImageSizeError("PNG file is too small to contain dimensions.")

    width, height = struct.unpack(">II", header[16:24])
    return width, height


def read_jpeg_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as file:
        file.read(2)
        while True:
            marker_start = file.read(1)
            if not marker_start:
                break
            if marker_start != b"\xff":
                continue

            marker = file.read(1)
            while marker == b"\xff":
                marker = file.read(1)

            if marker in {b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5", b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf"}:
                file.read(3)
                height, width = struct.unpack(">HH", file.read(4))
                return width, height

            length_bytes = file.read(2)
            if len(length_bytes) != 2:
                break
            segment_length = struct.unpack(">H", length_bytes)[0]
            file.seek(segment_length - 2, 1)

    raise ImageSizeError(f"Could not read JPEG dimensions: {path}")
