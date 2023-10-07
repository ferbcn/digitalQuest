import time
import json
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse

from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

app = FastAPI(title='WebsocketAPI')

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    current_level = 0
    return templates.TemplateResponse("index.html", {"request": request, "level": current_level})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)