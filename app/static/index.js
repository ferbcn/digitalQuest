document.addEventListener("DOMContentLoaded", function() {
    // Your entire JavaScript code here

    let terminal = document.getElementById("terminal");

    let ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    let wsUrl = ws_scheme + '://' + window.location.host + "/terminalws"
    let socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
        console.log("Message received: ", event.data);
        // Special commands received from server
        const data_array = event.data.split(" ");

        if (data_array[0] == "conninfo"){
            document.getElementById("conn-count").innerText = data_array[1];
        }

        else if (event.data == "clear"){
            terminal.innerText = "";
            addCursor(terminal);
        }
        else if (event.data == "exit"){
            console.log("bye!");
            location.reload();
        }
        // default behaviour: print text received from server
        else{
            let str = terminal.innerText;
            terminal.innerText = str.slice(0, -2);
            terminal.innerText += event.data;
            terminal.innerText += '$ '
            addCursor(terminal);
            // scroll to bottom of <div>
            terminal.scrollTop = terminal.scrollHeight;
        }

    };

    socket.onclose = function(event) {
        terminal.innerText = 'Connection lost!';
    };

    socket.onerror = function(error) {
        terminal.innerText = 'Error: ${error.message}';
    };

    socket.onopen = function(event) {
        terminal.innerText = 'Connection established!' + '\n$ ';
        //socket.send("ping");
        addCursor(terminal);
    };

    let command = "";
    document.addEventListener("keydown", (event) => {
        const key = event.key;
        //console.log(key);
        if (key === "Enter") {
            socket.send(command);
            newLine(terminal);
            addCursor(terminal);
            command = "";
        }
        else if (key === " ") {
            event.preventDefault();
            let str = terminal.innerText;
            terminal.innerText = str.slice(0, -1);
            terminal.innerHTML += "&nbsp;";
            command += " ";
            addCursor(terminal);
        }
        else if (key === "Shift") {
            // don't write when shift is pressed
        }
        else if (key === "Backspace") {
            let str = terminal.innerText;
            //console.log(command, command.length);
            slice_str = str.slice(0, -2);
            terminal.innerText = slice_str;
            command = command.slice(0, -1);
            addCursor(terminal);

        }
        else{
            command += key;
            let str = terminal.innerText;
            slice_str = str.slice(0, -1);
            terminal.innerText = slice_str + key;
            addCursor(terminal);
        }

        // catch line overflow
        if (command.length % 60 == 0 ){
            newLine(terminal);
            addCursor(terminal);
        }
    });

    // Keyboard Pop-Up for mobile devices on button press
    document.getElementById('openKeyboard').addEventListener('click', function(){
        var inputElement = document.getElementById('hiddenInput');
        inputElement.style.visibility = 'visible'; // unhide the input
        inputElement.focus(); // focus on it so keyboard pops
        inputElement.style.visibility = 'hidden'; // hide it again
    });

    var cursor = true;
    var speed = 250;
    setInterval(() => {
      if(cursor) {
        document.getElementById('cursor').style.opacity = 0;
        cursor = false;
      }else {
        document.getElementById('cursor').style.opacity = 1;
        cursor = true;
      }
    }, speed);

});

function addCursor (terminal) {
    let spanElement = document.createElement("span");
    spanElement.id = "cursor";
    spanElement.textContent = "█"; //█
    terminal.appendChild(spanElement);
}

function newLine (terminal) {
    let str = terminal.innerText;
    terminal.innerText = str.slice(0, -1);
    terminal.innerText += '\n';
}