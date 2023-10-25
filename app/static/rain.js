const characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
const windowWidth = window.innerWidth;
const windowHeight = window.innerHeight;
const columns = windowWidth;
//const columns = 1000;
const streams = [];
let canvas, ctx;

function setup() {
    canvas = document.getElementById('matrixCanvas');
    ctx = canvas.getContext('2d');

    for (let i = 0; i < windowWidth; i++) {
        streams[i] = {
            x: i*1,
            y: Math.floor(Math.random() * window.innerHeight),
            speed: Math.random() * 10,
            length: Math.floor(Math.random() * 3) + 1
        };
    }
}

function draw() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = 'green';
    ctx.font = '16px monospace';

    for (let i = 0; i < streams.length; i++) {
        const stream = streams[i];
        let text = '';

        for (let j = 0; j < stream.length; j++) {
            text += characters[Math.floor(Math.random() * characters.length)];
        }

        ctx.fillText(text, stream.x, stream.y);

        if (stream.y > canvas.height) {
            stream.y = 0;
        } else {
            stream.y += stream.speed;
        }
    }
}

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    //columns = canvas.width;
}

setup();
resizeCanvas();
setInterval(draw, 50);
window.addEventListener('resize', resizeCanvas);