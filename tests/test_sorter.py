from __future__ import annotations

import base64
from pathlib import Path

from fastapi.testclient import TestClient

from image_sorter.sorter import ImageBuffer, load_paths, move_image
from image_sorter.web import create_app

_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6X8BQAAAABJRU5ErkJggg=="
)


def make_image(path: Path) -> None:
    path.write_bytes(_PNG)


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


def test_web_flow(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    sel = tmp_path / "sel"
    unsel = tmp_path / "unsel"
    raw.mkdir()
    for i in range(3):
        make_image(raw / f"img{i}.jpg")
    app = create_app(raw, sel, unsel)
    client = TestClient(app)

    data = client.get("/next").json()
    assert not data["done"]

    client.post("/select", json={"selected": True})
    client.post("/select", json={"selected": False})
    client.post("/select", json={"selected": True})

    assert len(list(sel.iterdir())) == 2
    assert len(list(unsel.iterdir())) == 1
