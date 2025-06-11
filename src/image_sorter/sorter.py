from __future__ import annotations

import shutil
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from rich.traceback import install

install(show_locals=True)

BUFFER_SIZE = 32


@dataclass(slots=True)
class ImgRecord:
    path: Path
    data: bytes


def load_paths(raw_dir: Path) -> list[Path]:
    return sorted(p for p in raw_dir.iterdir() if p.is_file())


def load_image(path: Path) -> bytes:
    return path.read_bytes()


class ImageBuffer:
    def __init__(self, paths: list[Path], size: int = BUFFER_SIZE) -> None:
        self._iter = iter(paths)
        self._buf: deque[ImgRecord] = deque()
        self.size = size
        self._fill()

    def _fill(self) -> None:
        while len(self._buf) < self.size:
            try:
                p = next(self._iter)
            except StopIteration:
                break
            self._buf.append(ImgRecord(p, load_image(p)))

    def next(self) -> ImgRecord | None:
        if not self._buf:
            return None
        rec = self._buf.popleft()
        self._fill()
        return rec


def move_image(rec: ImgRecord, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / rec.path.name
    shutil.move(rec.path, target)
    return target


def sort_images(_: Path, __: Path, ___: Path) -> None:  # pragma: no cover - legacy
    logger.warning("OpenCV sorting deprecated; use web server instead")


def main() -> None:  # pragma: no cover - legacy
    logger.info("Run `image-sorter-web` for the web interface")


if __name__ == "__main__":  # pragma: no cover - legacy
    main()
