document.addEventListener('DOMContentLoaded', () => {
    const videoFeed = document.getElementById('videoFeed');
    const startButton = document.getElementById('startButton');
    const translationBox = document.getElementById('translationBox');
    const statusBox = document.getElementById('statusBox');

    let ws;
    let streamActive = false;
    let stream;

    async function captureFrame() {
        const canvas = document.createElement('canvas');
        canvas.width = videoFeed.videoWidth;
        canvas.height = videoFeed.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoFeed, 0, 0, canvas.width, canvas.height);
        const imageData = canvas.toDataURL('image/jpeg');
        return imageData.split(',')[1]; // Return base64 encoded image
    }

    function startCamera() {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then((mediaStream) => {
                stream = mediaStream;
                videoFeed.srcObject = mediaStream;
                streamActive = true;
                startButton.textContent = 'Stop Camera';
            })
            .catch((err) => {
                console.error("Error accessing the camera: ", err);
                statusBox.textContent = "Camera access error!";
            });
    }

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        videoFeed.srcObject = null;
        streamActive = false;
        startButton.textContent = 'Start Camera';
    }

    function startWebSocket() {
        ws = new WebSocket('ws://52.21.224.65:8000/ws');
        
        ws.onopen = function(event) {
            console.log('Connection opened', event);
            statusBox.textContent = "Connected!";
        };

        ws.onmessage = function(event) {
            translationBox.textContent = event.data;
        };

        ws.onerror = function(event) {
            console.error('WebSocket error observed:', event);
            statusBox.textContent = "Connection error!";
        };

        ws.onclose = function(event) {
            console.log('WebSocket connection closed:', event);
            statusBox.textContent = "Connection closed!";
        };
    }

    function stopWebSocket() {
        if (ws) {
            ws.close();
        }
    }

    startButton.addEventListener('click', () => {
        if (!streamActive) {
            startCamera();
            startWebSocket();
        } else {
            stopCamera();
            stopWebSocket();
        }
    });

    // Send frame to WebSocket every second if stream is active
    setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN && streamActive) {
            captureFrame().then(frame => {
                ws.send(JSON.stringify({ frame }));
            });
        }
    }, 1000); // Adjust interval as needed
});
