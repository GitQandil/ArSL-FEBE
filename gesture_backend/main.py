from fastapi import FastAPI, WebSocket, HTTPException
import cv2
import mediapipe as mp
import numpy as np
import base64
import asyncio
import time
import logging

app = FastAPI()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Gesture Recognition Setup
mp_tasks = mp.tasks
BaseOptions = mp_tasks.BaseOptions
GestureRecognizer = mp_tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp_tasks.vision.GestureRecognizerOptions
VisionRunningMode = mp_tasks.vision.RunningMode

class GestureRecognizerWrapper:
    def __init__(self):
        self.latest_result = None

        def result_callback(result, output_image, timestamp_ms):
            self.latest_result = result

        options = GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path='/home/admin/gesture_backend/gesture_recognizer.task'), # Update the path
            running_mode=VisionRunningMode.LIVE_STREAM,
            result_callback=result_callback
        )

        self.recognizer = GestureRecognizer.create_from_options(options)

    async def process_frame(self, frame_rgb, timestamp_ms):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        self.recognizer.recognize_async(mp_image, timestamp_ms)
        await asyncio.sleep(0.01)  # Small delay for async processing
        return self.latest_result

gesture_recognizer = GestureRecognizerWrapper()

@app.get("/")
def read_root():
    return {"message": "Gesture Recognition Server is running"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            frame_data = data.split(',')[1]
            frame_bytes = base64.b64decode(frame_data)
            frame_np = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_np, flags=1)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_timestamp_ms = int(time.time() * 1000)

            result = await gesture_recognizer.process_frame(frame_rgb, frame_timestamp_ms)

            result_text = "No gesture detected"
            if result is not None and result.gestures:
                result_text = f"Result: {result.gestures[0].category_name}"

            await websocket.send_text(result_text)
    except Exception as e:
        logging.error(f"WebSocket Error: {e}", exc_info=True)
        await websocket.close()

# Further routes and logic can be added here
