import json
import random

import uvicorn
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse

from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from typing import List

from starlette.websockets import WebSocketDisconnect

import os
import openai

app = FastAPI(title='TheDigitalQuest')

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

OPENAI_KEY = os.getenv("OPENAI_KEY")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        json_data = json.dumps({"type": "conn-info", "content": len(self.active_connections)})
        await self.broadcast(json_data)

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

@app.get("/rain", response_class=HTMLResponse)
def index(request: Request):
    current_level = 0
    return templates.TemplateResponse("rain.html", {"request": request})

# Websocket endpoint
@app.websocket("/wsconsole")
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
            if last_data == "<*bs*>":
                # remove last char from buffer
                command_buffer = command_buffer[:-1]
                mes_object = {"type": "system", "content": "nop"}

            # Process Special and Regular commands
            # Console History Operations
            elif last_data == "<*bck*>" or last_data == "<*fwd*>":
                mes_type = "history"
                if last_data == "<*bck*>":
                    if len(my_system.command_history) > 0:
                        command_buffer = my_system.command_history[-command_history_pos]
                    if len(my_system.command_history) > command_history_pos:
                        command_history_pos += 1
                elif last_data == "<*fwd*>":
                    if command_history_pos > 1:
                        command_history_pos -= 1
                    if command_history_pos >= 1:
                        command_buffer = my_system.command_history[-command_history_pos]

                mes_object = {"type": mes_type, "content": command_buffer}
                print("History:", my_system.command_history, command_buffer)

            # Process new command after newline
            elif last_data == "\n":
                if len(command_buffer) > 0:
                    my_system.command_history.append(command_buffer)
                    command_history_pos = 1
                    command_list = command_buffer.split(" ")
                    command_buffer = ""
                    mes_object = await process_command(websocket, command_list)
                else:
                    mes_object = {"type": "text", "content": "\n$"}

            # Read next char into command buffer
            else:
                command_buffer += last_data
                # echo character to websocket
                mes_object = {"type": "text", "content": last_data}

            await websocket.send_text(json.dumps(mes_object))

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def process_command(websocket, command_list):
    print("Commands and args: ", command_list)
    mes_type = "text" # default message type

    if command_list[0] == "hello":
        # await websocket.send_text("\nworld!\n$")
        mes_content = "\nworld!\n$"

        # Basic commands
    elif command_list[0] == "clear":
        mes_type = "system"
        mes_content = "clear"

    elif command_list[0] == "help":
        available_commands = ["help", "clear", "exit", "rand [int]", "cat [filename]", "AI [prompt]"]
        mes_content = "\nAvailable commands:\n" + "\n".join([com for com in available_commands]) + "\n$"
        mes_type = "text"

    elif command_list[0] == "exit":
        my_system.command_history = []
        mes_type = "system"
        mes_content = "exit"

    elif command_list[0] == "cat":
        filename = "linux.txt"
        if len(command_list) > 1:
            filename = command_list[1]
        try:
            filepath = "static/" + filename
            print(filepath)
            with open(filepath, "r") as text_file:
                mes_content = "\n"
                mes_content += text_file.read()
                mes_content += "\n$"
                print(mes_content)
        except Exception as e:
            mes_content = f"\nFile does not exist!\n$"

    elif command_list[0] == "rand":
        try:
            length = int(command_list[1])
        except Exception:
            length = 64
        mes_content = f"\n$"
        rand_str = ""
        for i in range(length):
            rand_str += chr(random.randint(64, 128))
        mes_content += f"{rand_str}\n$"

    elif command_list[0] == "AI":
        prompt = " ".join([com for com in command_list[1:]])
        print(prompt)

        openai.api_key = os.getenv("OPENAI_KEY")
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=100,
            temperature=0
        )
        answer = response["choices"][0]["text"]
        mes_content = f"{answer}\n$"

    # Non commands
    else:
        mes_content = "\nUnknown command!\n$"

    # await websocket.send_text(json.dumps({"type": mes_type, "content": mes_content}))
    return {"type": mes_type, "content": mes_content}


def calc_fib(num):
    if num <= 0:
        return 0
    elif num <= 1:
        return 1
    else:
        return calc_fib(num-1) + calc_fib(num-2)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)