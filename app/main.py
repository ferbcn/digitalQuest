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


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.broadcast("conninfo " + str(len(self.active_connections)))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except WebSocketDisconnect:
                self.disconnect(connection)


manager = ConnectionManager()


class FileSystem:
    def __init__(self):
        with open("static/dir_tree.json", "r") as dir_json:
            self.dir_tree = json.load(dir_json)
        with open("static/files.json", "r") as files_json:
            self.files = json.load(files_json)
        self.current_dir = "/"
        self.current_user = "root"
        self.available_dirs = []
        self.available_files = []
        self.command_history = []

        self.command_list = {}

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


my_system = FileSystem()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    current_level = 0
    return templates.TemplateResponse("index.html", {"request": request, "level": current_level})


# Websocket endpoint
@app.websocket("/terminalws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        my_system.set_current_dir("/")
        command_buffer = ""
        command_history_pos = 1
        # await for messages and send messages
        while True:
            last_data = await websocket.receive_text()

            # Backspace Operation
            if last_data == "<<<bs>>>":
                command_buffer = command_buffer[:-1]
            elif last_data == "<<<bck>>>":
                if len(my_system.command_history) > 0:
                    command_buffer = my_system.command_history[-command_history_pos]
                    await websocket.send_text("hist" + " " + command_buffer)
                    print("History:", my_system.command_history, command_buffer)
                if len(my_system.command_history) > command_history_pos:
                    command_history_pos += 1
            elif last_data == "<<<fwd>>>":
                if command_history_pos > 1:
                    command_history_pos -= 1
                if command_history_pos >= 1:
                    command_buffer = my_system.command_history[-command_history_pos]
                    await websocket.send_text("hist" + " " + command_buffer)
                    print("History:", my_system.command_history, command_buffer)

            # Process new command after newline
            elif last_data == "\n":
                if len(command_buffer) > 0:
                    my_system.command_history.append(command_buffer)
                    command_history_pos = 1
                    command_list = command_buffer.split(" ")
                    await process_command(websocket, command_list)
                    command_buffer = ""
                else:
                    await websocket.send_text(f"\n$")

            # Read next char into command buffer
            else:
                command_buffer += last_data
                await websocket.send_text(last_data)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def process_command(websocket, command_list):
    print("Commands and args: ", command_list)
    if command_list[0] == "ping":
        await websocket.send_text("\npong\n$")

    elif command_list[0] == "hello":
        await websocket.send_text("\nworld!\n$")

        # Basic commands
    elif command_list[0] == "clear":
        await websocket.send_text("clear")

    elif command_list[0] == "help":
        available_commands = ["help", "clear", "exit", "ls", "cwd", "cd [dir]", "cat [file]"]
        command_list_str = "\nAvailable commands:\n" + "\n".join([com for com in available_commands]) + "\n$"
        await websocket.send_text(command_list_str)

    elif command_list[0] == "exit":
        my_system.command_history = []
        await websocket.send_text("exit")

    elif command_list[0] == "ls":
        output = f"\nDirectory content of {my_system.current_dir}: \n" \
                 "Name / Type: \n"
        output += my_system.get_all() + "$"
        await websocket.send_text(output)

    elif command_list[0] == "cd":
        if len(command_list) > 1:
            if command_list[1] == "..":
                target_dir = my_system.get_parent_dir()
            else:
                target_dir = command_list[1]
        else:
            target_dir = "/"

        if target_dir in my_system.available_dirs:
            my_system.set_current_dir(target_dir)
            await websocket.send_text(f"\nChanged to: {target_dir} \n$")
        else:
            await websocket.send_text(f"\n{target_dir} not found or not a directory!\n")

    elif command_list[0] == "cwd":
        await websocket.send_text(f"\nCurrent dir: {my_system.current_dir}\n$")

    # Advanced commands
    elif command_list[0] == "cat":
        if len(command_list) > 1:
            target_file = command_list[1]
            if target_file in my_system.available_files:
                file = my_system.files.get(target_file).get("content")
                if file.get("owner") == my_system.current_user:
                    await websocket.send_text("\n" + file.get("data") + "\n$")
                else:
                    await websocket.send_text("\nNot authorized! \n$")
            else:
                await websocket.send_text(f"\n{target_file} not found!\n$")
        else:
            await websocket.send_text(f"\nUsage: 'cat [file]'\n$")

    elif command_list[0] == "fib":
        if len(command_list) > 1:
            num = int(command_list[1])
            if num < 40:
                result = calc_fib(num)
                await websocket.send_text(f"\nResult: {result}\n$")
            else:
                await websocket.send_text(f"\nPlease input an integer between 0 and 40.\n$")
        else:
            await websocket.send_text(f"\nUsage: 'cat [file]'\n$")

    # Non commands
    else:
        await websocket.send_text("\nUnknown command!\n$")


def calc_fib(num):
    if num <= 0:
        return 0
    elif num <= 1:
        return 1
    else:
        return calc_fib(num-1) + calc_fib(num-2)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)