from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from image_sorter.sorter import ImageBuffer, load_paths, move_image


def make_image(path: Path) -> None:
    arr = np.zeros((10, 10, 3), dtype=np.uint8)
    cv2.imwrite(str(path), arr)


def test_move_image(tmp_path: Path) -> None:
    src = tmp_path / "raw"
    dst = tmp_path / "dst"
    src.mkdir()
    img = src / "a.jpg"
    make_image(img)
    rec = ImageBuffer([img]).next()
    assert rec
    target = move_image(rec, dst)
    assert target.exists()
    assert not img.exists()


def test_buffer(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    paths = []
    for i in range(40):
        p = raw / f"img{i}.jpg"
        make_image(p)
        paths.append(p)
    buf = ImageBuffer(load_paths(raw))
    seen = 0
    while rec := buf.next():
        assert rec.path.exists()
        seen += 1
    assert seen == 40
