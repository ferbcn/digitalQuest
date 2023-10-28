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

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    current_level = 0
    return templates.TemplateResponse("index.html", {"request": request, "level": current_level})


@app.get("/rain", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("rain.html", {"request": request})


# Websocket endpoint
@app.websocket("/wsconsole")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        command_buffer = ""
        command_history_pos = 1
        command_history = []
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
                    if len(command_history) > 0:
                        command_buffer = command_history[-command_history_pos]
                    if len(command_history) > command_history_pos:
                        command_history_pos += 1
                elif last_data == "<*fwd*>":
                    if command_history_pos > 1:
                        command_history_pos -= 1
                    if command_history_pos >= 1:
                        command_buffer = command_history[-command_history_pos]

                mes_object = {"type": mes_type, "content": command_buffer}
                print("History:", command_history, command_buffer)

            # Process new command after newline
            elif last_data == "\n":
                if len(command_buffer) > 0:
                    command_history.append(command_buffer)
                    command_history_pos = 1
                    command_list = command_buffer.split(" ")
                    command_buffer = ""
                    mes_object = await process_command(command_list)
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


async def process_command(command_list):
    print("Command and args: ", command_list)
    mes_type = "text"   # default message type
    filepath = "static/files/"

    command = command_list[0]

    if command == "hello":
        # await websocket.send_text("\nworld!\n$")
        mes_content = "\nworld!\n$"

        # Basic commands
    elif command == "cls":
        mes_type = "system"
        mes_content = "clear"

    elif command == "help":
        available_commands = ["help: this message",
                              "cls: clear screen",
                              "exit: restart console",
                              "rand [n]: print random string of length n",
                              "ls: list files",
                              "cat [filename]: print file content",
                              "ai [prompt]: ask something to an AI"]
        mes_content = "\nAvailable commands:\n" + "\n".join([com for com in available_commands]) + "\n$"
        mes_type = "text"

    elif command == "ls":
        files = os.listdir(filepath)
        mes_content = "\nAvailable files:\n" + "\n".join([f for f in files]) + "\n$"
        mes_type = "text"

    elif command == "exit":
        mes_type = "system"
        mes_content = "exit"

    elif command == "cat":
        filename = "linux.txt"
        if len(command_list) > 1:
            filename = command_list[1]
            filename = filename.replace("/", "")    # Input sanitation avoids reading upper directories
        try:
            filepath = "static/files/" + filename
            print(filepath)
            with open(filepath, "r") as text_file:
                mes_content = "\n"
                mes_content += text_file.read()
                mes_content += "\n$"
                print(mes_content)
        except Exception as e:
            mes_content = f"\nFile does not exist!\n$"

    elif command == "rand":
        try:
            length = int(command_list[1])
        except Exception:
            length = 64
        mes_content = f"\n$"
        rand_str = ""
        for i in range(length):
            rand_str += chr(random.randint(64, 128))
        mes_content += f"{rand_str}\n$"

    elif command == "ai":
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


if __name__ == "__main__":

    uvicorn.run(app, host="127.0.0.1", port=8000)