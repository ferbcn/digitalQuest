document.addEventListener("DOMContentLoaded", function() {
    // Your entire JavaScript code here

    let terminal = document.getElementById("terminal");

    let ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    let wsUrl = ws_scheme + '://' + window.location.host + "/terminalws"
    let socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
        console.log(event.data);
        terminal.innerText += "> " + event.data + '\r';
        terminal.scrollTop = terminal.scrollHeight;
    };

    socket.onclose = function(event) {
        terminal.innerText = 'Connection lost';
    };

    socket.onerror = function(error) {
        terminal.innerText = `Error: ${error.message}`;
    };

    socket.onopen = function(event) {
        terminal.innerText = 'Connection established!' + '\r';
        socket.send("ping");
    };

    let command = "";
    document.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            terminal.innerText += '\r';
            socket.send(command);
            command = "";
        }
        else{
            const key = event.key;
            command += key;
            terminal.innerText += key;
        }
    });

});
