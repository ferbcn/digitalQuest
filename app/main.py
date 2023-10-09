import time
import json
import uvicorn
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse

from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from typing import List

from starlette.websockets import WebSocketDisconnect

app = FastAPI(title='TheDigitalQuest')

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

dir_tree = {
    "/": {"parent_dir": None, "content": [{"name": "file1", "type": "file"}, {"name": "dir1", "type": "dir"}]},
    "dir1": {"parent_dir": "/", "content": [{"name": "file2", "type": "file"}, {"name": "file3", "type": "file"}]}
}


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: str):
        for connection in self.active_connections:
            #print("Sendig JSON data:", data)
            try:
                await connection.send_text(data)
            except WebSocketDisconnect:
                self.disconnect(connection)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    current_level = 0
    return templates.TemplateResponse("index.html", {"request": request, "level": current_level})




# Websocket endpoint
@app.websocket("/terminalws")
async def websocket_endpoint(websocket: WebSocket):
    current_dir = "/"
    available_dirs = [item.get("name") for item in dir_tree.get(current_dir).get("content") if item.get("type") == "dir"]
    available_dirs.append(dir_tree.get(current_dir).get("parent_dir"))

    await manager.connect(websocket)
    try:
        # await for messages and send messages
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "clear":
                await websocket.send_text("clear")
            elif data == "help":
                available_commands = ["help", "clear", "exit", "ls", "cwd"]
                command_list_str = "Command list:\n" + "\n".join([com for com in available_commands])
                await websocket.send_text(command_list_str)
            elif data == "hello":
                await websocket.send_text("world!")
            elif data == "exit":
                await websocket.send_text("exit")
            elif data == "ls":
                output = f"Directory content of {current_dir}: \r" \
                         "Name / Type: \r"
                for item in dir_tree.get(current_dir).get("content"):
                    output += item.get("name") + " / " + item.get("type") + "\r"
                await websocket.send_text(output)
            elif data[:3] == "cd ":
                target_dir = data[3:]
                if target_dir in available_dirs:
                    current_dir = target_dir
                    available_dirs = [item.get("name") for item in dir_tree.get(current_dir).get("content") if item.get("type") == "dir"]
                    available_dirs.append(dir_tree.get(current_dir).get("parent_dir"))
                    await websocket.send_text(f"Changed to: {target_dir}")
                else:
                    await websocket.send_text(f"{target_dir} not found!")
            elif data == "cwd":
                await websocket.send_text(f"Current dir: {current_dir}")
            else:
                await websocket.send_text("Unknown command!")

    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)