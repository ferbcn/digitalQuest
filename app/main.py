import time
import json
import subprocess
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
            try:
                await connection.send_text(data)
            except WebSocketDisconnect:
                self.disconnect(connection)


class Session:
    def __init__(self):
        with open ("dir_tree.json", "r") as dir_json:
            self.dir_tree = json.load(dir_json)
        with open ("files.json", "r") as files_json:
            self.files = json.load(files_json)
        self.current_dir = "/"
        self.current_user = "root"
        self.available_dirs = []
        self.available_files = []

    def get_all(self):
        output = ""
        for item in self.dir_tree.get(self.current_dir).get("content"):
            output += item.get("name") + " / " + item.get("type") + "\n"
        return output

    def get_dirs(self):
        available_dirs = [item.get("name") for item in self.dir_tree.get(self.current_dir).get("content") if
                          item.get("type") == "dir"]
        available_dirs.append(self.dir_tree.get(self.current_dir).get("parent_dir"))
        available_dirs.append("/")
        return available_dirs

    def get_files(self):
        available_files = [item.get("name") for item in self.dir_tree.get(self.current_dir).get("content") if
                           item.get("type") == "file"]
        return available_files

    def get_parent_dir(self):
        return self.dir_tree.get(self.current_dir).get("parent_dir")

    def set_current_dir(self, dir):
        self.current_dir = dir
        self.available_dirs = self.get_dirs()
        self.available_files = self.get_files()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    current_level = 0
    return templates.TemplateResponse("index.html", {"request": request, "level": current_level})


# Websocket endpoint
@app.websocket("/terminalws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        session.set_current_dir("/")
        # await for messages and send messages
        while True:
            data = await websocket.receive_text()
            command_list = data.split(" ")

            # Test massages
            if command_list[0] == "ping":
                await websocket.send_text("pong\n")
            elif command_list[0] == "hello":
                await websocket.send_text("world!\n")

            # Basic commands
            elif command_list[0] == "clear":
                await websocket.send_text("clear")
            elif command_list[0] == "help":
                available_commands = ["help", "clear", "exit", "ls", "cwd", "cd [dir]", "cat [file]"]
                command_list_str = "Available commands:\n" + "\n".join([com for com in available_commands]) + "\n"
                await websocket.send_text(command_list_str)
            elif command_list[0] == "exit":
                await websocket.send_text("exit")
            elif command_list[0] == "ls":
                output = f"Directory content of {session.current_dir}: \n" \
                         "Name / Type: \n"
                output += session.get_all()
                await websocket.send_text(output)
            elif command_list[0] == "cd":
                if len(command_list) > 1:
                    if command_list[1] == "..":
                        target_dir = session.get_parent_dir()
                    else:
                        target_dir = command_list[1]
                else:
                    target_dir = "/"

                if target_dir in session.available_dirs:
                    session.set_current_dir(target_dir)
                    await websocket.send_text(f"Changed to: {target_dir} \n")
                else:
                    await websocket.send_text(f"{target_dir} not found or not a directory!\n")

            elif data == "cwd":
                await websocket.send_text(f"Current dir: {session.current_dir}\n")

            # Advanced commands
            elif command_list[0] == "cat" and len(command_list) > 1:
                target_file = command_list[1]
                if target_file in session.available_files:
                    file = session.files.get(target_file).get("content")
                    if file.get("owner") == session.current_user:
                        await websocket.send_text(file.get("data") + "\n")
                    else:
                        await websocket.send_text("Not authorized! \n")
                else:
                    await websocket.send_text(f"{target_file} not found!\n")

            # Non commands
            elif command_list[0] == "":
                await websocket.send_text(f"")

            else:
                await websocket.send_text("Unknown command!\n")

    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    manager = ConnectionManager()
    session = Session()
    uvicorn.run(app, host="0.0.0.0", port=8000)