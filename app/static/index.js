document.addEventListener("DOMContentLoaded", function() {
    // Your entire JavaScript code here

    let terminal = document.getElementById("terminal");

    let ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    let wsUrl = ws_scheme + '://' + window.location.host + "/terminalws"
    let socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
        console.log("Message received: ", event.data);
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
        const key = event.key;
        //console.log(key);
        if (key === "Enter") {
            terminal.innerText += '\r';
            socket.send(command);
            command = "";
        }
        else if (key === " ") {
            event.preventDefault();
            terminal.innerHTML += "&nbsp;";
            command += " ";
        }
        else if (key === "Shift") {
            // don't write when shift is pressed
        }
        else if (key === "Backspace") {
            let str = terminal.innerText;
            slice_str = str.slice(0, -1);
            terminal.innerText = slice_str;
            command = command.slice(0, -1);
        }
        else{
            command += key;
            terminal.innerText += key;
        }
    });

    // Keyboard Pop-Up for mobile devices
    document.getElementById('openKeyboard').addEventListener('click', function(){
        var inputElement = document.getElementById('hiddenInput');
        inputElement.style.visibility = 'visible'; // unhide the input
        inputElement.focus(); // focus on it so keyboard pops
        inputElement.style.visibility = 'hidden'; // hide it again
    });

});
