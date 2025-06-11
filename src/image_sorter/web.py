from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.responses import HTMLResponse
from loguru import logger
from pydantic import BaseModel
from rich.traceback import install

from .sorter import ImageBuffer, ImgRecord, load_paths, move_image

install(show_locals=True)


class SelectReq(BaseModel):
    selected: bool


INDEX_HTML = """<!DOCTYPE html>
<html>
<head><meta charset='utf-8'><title>Image Sorter</title></head>
<body>
<img id='img' style='max-width:100%;'/>
<script>
let cur="";
async function next(){
  const r=await fetch('/next');
  const d=await r.json();
  if(d.done){document.body.innerHTML='<h1>Done</h1>';return;}
  cur=d.id;document.getElementById('img').src='data:image/jpeg;base64,'+d.data;
}
async function send(sel){
  const opts={
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({selected:sel})
  };
  const r=await fetch('/select',opts);
  const d=await r.json();
  if(d.done){document.body.innerHTML='<h1>Done</h1>';return;}
  cur=d.id;document.getElementById('img').src='data:image/jpeg;base64,'+d.data;
}
window.onload=next;
window.onkeydown=e=>{if(e.key==='1')send(true);if(e.key==='2')send(false);};
</script>
</body></html>"""


def _to_resp(rec: ImgRecord) -> dict[str, str | bool]:
    data = base64.b64encode(rec.data).decode()
    return {"done": False, "id": rec.path.name, "data": data}


@dataclass(slots=True)
class SortState:
    raw_dir: Path
    selected_dir: Path
    unselected_dir: Path
    buffer: ImageBuffer
    current: ImgRecord | None = None

    def next(self) -> ImgRecord | None:
        self.current = self.buffer.next()
        return self.current

    def select(self, selected: bool) -> ImgRecord | None:
        if not self.current:
            return None
        dest = self.selected_dir if selected else self.unselected_dir
        move_image(self.current, dest)
        return self.next()


def create_app(raw: Path, sel: Path, unsel: Path) -> FastAPI:
    state = SortState(raw, sel, unsel, ImageBuffer(load_paths(raw)))
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return INDEX_HTML

    @app.get("/next")
    async def get_next() -> dict[str, str | bool]:
        rec = state.next()
        return {"done": True} if rec is None else _to_resp(rec)

    BODY = Body(...)

    @app.post("/select")
    async def select(req: SelectReq = BODY) -> dict[str, str | bool]:
        rec = state.select(req.selected)
        return {"done": True} if rec is None else _to_resp(rec)

    return app


def run() -> None:  # pragma: no cover - manual start
    app = create_app(Path("raw_images"), Path("selected"), Path("unselected"))
    logger.info("Open http://localhost:8000 in your browser")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":  # pragma: no cover - manual
    run()
