document.addEventListener("DOMContentLoaded", function() {

    let terminal = document.getElementById("terminal");

    let ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    let wsUrl = ws_scheme + '://' + window.location.host + "/terminalws"
    let socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
        const all_data = event.data;
        console.log("Message received: ", all_data);

        // Special commands received from server
        const data_array = event.data.split(" ");
        console.log(data_array);
        if (data_array[0] == "conninfo"){
            document.getElementById("conn-count").innerText = data_array[1];
        }

        else if (data_array[0] == "clear"){
            terminal.innerText = "$";
            addCursor(terminal);
        }
        else if (data_array[0] == "exit"){
            console.log("bye!");
            location.reload();
        }

        // default behaviour: print text received from server
        else{
            let str = terminal.innerText;
            terminal.innerText = str.slice(0, -2);
            terminal.innerText += all_data;
            terminal.innerText += '$'
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
        terminal.innerText = 'Connection established!' + '\n$';
        addCursor(terminal);
    };


    document.addEventListener("keydown", (event) => {
        //console.log(event);
        const key = event.key;

        if (key === "Enter") {
            terminal.innerText += "\r";
            socket.send("\n");
        }

        else if (key === " ") {
            event.preventDefault();
            socket.send(" ");
            let str = terminal.innerText;
            terminal.innerText = str.slice(0, -1);
            terminal.innerHTML += "&nbsp;";
            addCursor(terminal);
        }

        else if (key === "Shift") {
            // don't write when shift is pressed
        }

        else if (key === "Backspace") {
            socket.send("B*S\n");
            terminal.innerText = terminal.innerText.slice(0, -2);
            addCursor(terminal);
        }

        else if (key === "ArrowUp") {
                socket.send("hist_back");
            }
        else if (key === "ArrowDown") {
                socket.send("hist-fwd");
            }

        // Default behaviour: read char into command buffer and print char to screen
        else{
            socket.send(key);
            terminal.innerText = terminal.innerText.slice(0, -1);
            terminal.innerText += key;
            addCursor(terminal);
        }

        // catch line overflow
        if (command.length % 60 == 0 ){
            newLine(terminal);
            addCursor(terminal);
        }
    });

    // Keyboard Pop-Up for mobile devices on button press
    document.getElementById('terminal').addEventListener('click', function(){
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