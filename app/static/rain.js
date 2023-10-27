const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789カオシュンタカオ';
const windowWidth = window.innerWidth;
const windowHeight = window.innerHeight;
var columns = windowWidth;
const colorArray = ["green", "firebrick", "purple", "skyblue", "lightgrey"];
var colorIndex = 0;
var charColor = colorArray[colorIndex];
var run_anim = true;

const streams = [];
let canvas, ctx;

function setup() {
    canvas = document.getElementById('matrixCanvas');
    ctx = canvas.getContext('2d');

    for (let i = 0; i < columns; i++) {
        streams[i] = {
            x: i*1,
            y: Math.floor(Math.random() * window.innerHeight),
            speed: Math.random() * 10,
            length: Math.floor(Math.random() * 3) + 1,
            text: ""
        };
    }
}

function draw() {
    if (run_anim){
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = charColor;
        ctx.font = '16px monospace';

        for (let i = 0; i < streams.length; i++) {

            const stream = streams[i];
            let text = '';

            for (let j = 0; j < stream.length; j++) {
                text += characters[Math.floor(Math.random() * characters.length)];
            }

            stream.text = text;
            ctx.fillText(text, stream.x, stream.y);

            if (stream.y > canvas.height) {
                stream.y = 0;
            } else {
                stream.y += stream.speed;
            }
        }
    }
}

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}


// Detect a click on the entire document
document.addEventListener('dblclick', function(event) {
    // Code to run when any part of the document is clicked
    charColor = colorArray[colorIndex];
    colorIndex++;
    if (colorIndex >= colorArray.length) colorIndex = 0;
});

// Detect window resize and redraw animation canvas
window.addEventListener('resize', function() {
    // Code to run when the window is resized
    columns = window.innerWidth;
    console.log(columns);
    setup();
    resizeCanvas();
});

// Mouse move event
document.addEventListener('mousemove', function(event) {
    const x = event.clientX;
    const y = event.clientY;
    //console.log(`Mouse coordinates - X: ${x}, Y: ${y}`);
    ctx.fillStyle = colorArray[(colorIndex+1) % colorArray.length];
    for (let i = 0; i < streams.length; i++) {
        const stream = streams[i];
        let radius = 50;
        if (stream.x > x-radius && stream.x < x+radius) {
            if (stream.y > y-radius && stream.y < y+radius){
                ctx.fillText(stream.text, stream.x, stream.y);
            }
        }
    }
});

// Change digital rain colors according to key strokes on keyboard
document.addEventListener("keydown", (event) => {
    const key = event.key.toUpperCase();
    ctx.fillStyle = colorArray[(colorIndex+1) % colorArray.length];
    for (let i = 0; i < streams.length; i++) {
        const stream = streams[i];
        if (stream.text.indexOf(key) > -1) {
            ctx.fillText(stream.text, stream.x, stream.y);
        }
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const toggleSwitch = document.getElementById("switch");
    const content = document.querySelector(".content");

    toggleSwitch.addEventListener("click", function () {
        if (run_anim) run_anim = false;
        else run_anim = true;
    });
});

setup();
resizeCanvas();
setInterval(draw, 50);
window.addEventListener('resize', resizeCanvas);