from __future__ import annotations

import shutil
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import cv2
from loguru import logger
from rich.traceback import install

install(show_locals=True)

BUFFER_SIZE = 32


@dataclass(slots=True)
class ImgRecord:
    path: Path
    img: cv2.typing.MatLike


def load_paths(raw_dir: Path) -> list[Path]:
    return sorted(p for p in raw_dir.iterdir() if p.is_file())


def load_image(path: Path) -> cv2.typing.MatLike:
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(path)
    return img


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


def sort_images(raw_dir: Path, sel_dir: Path, unsel_dir: Path) -> None:
    paths = load_paths(raw_dir)
    if not paths:
        logger.info("no images found in {}", raw_dir)
        return

    buf = ImageBuffer(paths)
    cv2.namedWindow("image-sorter", cv2.WINDOW_NORMAL)
    while rec := buf.next():
        cv2.imshow("image-sorter", rec.img)
        while True:
            key = cv2.waitKey(0)
            if key == ord("1"):
                move_image(rec, sel_dir)
                break
            if key == ord("2"):
                move_image(rec, unsel_dir)
                break
            if key == 27:  # ESC
                cv2.destroyAllWindows()
                return
    cv2.destroyAllWindows()


def main() -> None:
    raw = Path("raw_images")
    sel = Path("selected")
    unsel = Path("unselected")
    sort_images(raw, sel, unsel)


if __name__ == "__main__":
    main()
