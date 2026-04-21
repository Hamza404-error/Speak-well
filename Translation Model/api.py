from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import cv2
import mediapipe as mp
import numpy as np
import base64
import os

from ASL import HandDetector, ASLClassifier
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = HandDetector()
translator = ASLClassifier()
landmarker = None

@app.on_event("startup")
def startup_event():
    global landmarker
    if not translator.train_model("asl_data_real.csv"):
        print("Could not train ASL model yet. Add data.")
    detector.train_model("hand_detection_data.csv")

    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
    landmarker = vision.HandLandmarker.create_from_options(options)
    print("Models initialized successfully!")

@app.websocket("/ws/translate")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    detector.history = []
    try:
        while True:
            data = await websocket.receive_text()
            
            if ',' in data:
                data = data.split(',')[1]
            try:
                img_data = base64.b64decode(data)
                nparr = np.frombuffer(img_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except Exception:
                continue
                
            if image is None:
                continue

            image = cv2.flip(image, 1)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
            results = landmarker.detect(mp_image)
            
            features = []
            translation = "?"
            
            if results.hand_landmarks:
                hand_landmarks = results.hand_landmarks[0]
                h, w, c = image.shape
                x_max, y_max = 0, 0
                x_min, y_min = w, h
                
                for lm in hand_landmarks:
                    x, y = int(lm.x * w), int(lm.y * h)
                    if x > x_max: x_max = x
                    if x < x_min: x_min = x
                    if y > y_max: y_max = y
                    if y < y_min: y_min = y
                
                box_w = max(x_max - x_min, 1)
                box_h = max(y_max - y_min, 1)
                
                for lm in hand_landmarks:
                    rel_x = (lm.x * w - x_min) / box_w
                    rel_y = (lm.y * h - y_min) / box_h
                    features.extend([rel_x, rel_y])

                current_wrist = (hand_landmarks[0].x, hand_landmarks[0].y)
                current_index = (hand_landmarks[8].x, hand_landmarks[8].y)
                
                if not hasattr(detector, 'history'):
                    detector.history = []
                    
                detector.history.append((current_wrist, current_index))
                if len(detector.history) > 10:
                    detector.history.pop(0)
                    
                wrist_dx, wrist_dy, index_dx, index_dy = 0.0, 0.0, 0.0, 0.0
                if len(detector.history) == 10:
                    old_w, old_i = detector.history[0]
                    wrist_dx = current_wrist[0] - old_w[0]
                    wrist_dy = current_wrist[1] - old_w[1]
                    index_dx = current_index[0] - old_i[0]
                    index_dy = current_index[1] - old_i[1]
                    
                features.extend([wrist_dx, wrist_dy, index_dx, index_dy])

                if len(features) == 46:
                    if not detector.is_hand(features):
                        cv2.putText(image, "Object ignored (Not a Hand)", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    else:
                        HAND_CONNECTIONS = [
                            (0,1), (1,2), (2,3), (3,4),
                            (0,5), (5,6), (6,7), (7,8),
                            (0,9), (9,10), (10,11), (11,12),
                            (0,13), (13,14), (14,15), (15,16),
                            (0,17), (17,18), (18,19), (19,20)
                        ]
                        for conn in HAND_CONNECTIONS:
                            p1, p2 = hand_landmarks[conn[0]], hand_landmarks[conn[1]]
                            x1, y1 = int(p1.x * w), int(p1.y * h)
                            x2, y2 = int(p2.x * w), int(p2.y * h)
                            cv2.line(image, (x1, y1), (x2, y2), (0, 255, 255), 2)
                        
                        for lm in hand_landmarks:
                            x, y = int(lm.x * w), int(lm.y * h)
                            cv2.circle(image, (x, y), 4, (0, 0, 255), -1)
                        
                        translation = translator.predict(features)
            else:
                cv2.putText(image, "No skeleton located", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

            # Re-encode image to base64 jpeg
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 70])
            b64_image = base64.b64encode(buffer).decode('utf-8')
            
            await websocket.send_json({
                "image": b64_image,
                "translation": translation,
                "skeleton_found": bool(results.hand_landmarks)
            })
            
    except WebSocketDisconnect:
        print("Client disconnected.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
