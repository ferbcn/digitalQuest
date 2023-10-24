document.addEventListener("DOMContentLoaded", function() {

    var prev_comm_length = 0; // needed to keep track of how many characters to delete from console
    var chars_in_line = 0; // keep track of number of chars in current line

    let terminal = document.getElementById("terminal");

    let ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    let wsUrl = ws_scheme + '://' + window.location.host + "/wsconsole";
    let socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {

        const data_in = event.data;
        const jsonData = JSON.parse(data_in);
        var type = jsonData.type;
        var content = jsonData.content;
        // console.log("Message: ", type, content);

        if (type == "conn-info"){
            document.getElementById("conn-count").innerText = content;
        }

        else if (type == "system"){
            if (content == "clear"){
                terminal.innerText = "$";
                addCursor(terminal);
            }
            else if (content == "exit"){
                console.log("bye!");
                location.reload();
            }
        }

        else if (type == "history"){
            let new_comm = content;
            terminal.innerText = terminal.innerText.slice(0, -(1 + prev_comm_length));
            prev_comm_length = new_comm.length;
            terminal.innerText += new_comm;
            addCursor(terminal);
        }

        // default behaviour: print chars received from server
        else if (type == "text"){
            terminal.innerText = terminal.innerText.slice(0, -1);
            prev_comm_length = 0;
            let t = terminal.innerText;
            for (const char of content) {
                if (char == " "){
                    terminal.innerHTML += "&nbsp";
                }
                else{
                    terminal.innerText += char;
                }
                chars_in_line += 1;
            }

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

        // console.log(event);
        const key = event.key;

        if (key === "Enter") {
            chars_in_line = 0;
            socket.send("\n");
            terminal.scrollTop = terminal.scrollHeight;
        }

        else if (key === " ") {
            event.preventDefault();
            socket.send(key);
        }

        else if (key === "Shift") {
            // don't write when shift is pressed
        }

        else if (key === "Backspace") {
            if (chars_in_line > 0){
                chars_in_line -= 1;
                socket.send("<*bs*>");
                terminal.innerText = terminal.innerText.slice(0, -2);
                addCursor(terminal);
            }
        }

        else if (key === "ArrowUp") {
            event.preventDefault();
            socket.send("<*bck*>");
        }
        else if (key === "ArrowDown") {
            event.preventDefault();
            socket.send("<*fwd*>");
        }

        else {
            socket.send(key);
        }

    });

    // Keyboard Pop-Up for mobile devices on button press
    document.getElementById('terminal').addEventListener('click', function(){
        var inputElement = document.getElementById('hiddenInput');
        inputElement.style.visibility = 'visible'; // unhide the input
        inputElement.focus(); // focus on it so keyboard pops
        inputElement.style.visibility = 'hidden'; // hide it again
    });

    // blinking cursor animation
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