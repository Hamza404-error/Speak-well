from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import cv2
import mediapipe as mp

import numpy as np
import base64
import os
import threading
from queue import Queue

tts_queue = Queue()

def tts_worker():
    # Direct Windows SAPI5 COM object bypasses pyttsx3 threading bugs
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    # SAPI rates go from -10 to 10. 0 is default, -1 is slightly slower
    speaker.Rate = -1 
    
    while True:
        text = tts_queue.get()
        if text is None:
            break
        speaker.Speak(text)
        tts_queue.task_done()

# Start TTS worker in background so it doesn't block video stream
threading.Thread(target=tts_worker, daemon=True).start()

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
pose_landmarker = None

@app.on_event("startup")
def startup_event():
    global landmarker
    if not translator.train_model("asl_data_real.csv"):
        print("Could not train ASL model yet. Add data.")
    detector.train_model("hand_detection_data.csv")

    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=2)
    landmarker = vision.HandLandmarker.create_from_options(options)
    
    pose_url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    import urllib.request
    if not os.path.exists("pose_landmarker.task"):
        print("Downloading pose model...")
        urllib.request.urlretrieve(pose_url, "pose_landmarker.task")

    global pose_landmarker
    base_options_pose = python.BaseOptions(model_asset_path='pose_landmarker.task')
    options_pose = vision.PoseLandmarkerOptions(base_options=base_options_pose)
    pose_landmarker = vision.PoseLandmarker.create_from_options(options_pose)
    print("Models initialized successfully!")

@app.websocket("/ws/translate")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    detector.history = []
    prediction_buffer = []
    last_spoken = ""
    
    # Macro States
    last_translations = [] # list of (word, timestamp)
    macro_state = "IDLE"
    fingerspell_word = ""
    last_letter_time = 0.0
    
    try:
        while True:
            data = await websocket.receive_text()
            
            mode = "translation"
            target = ""
            
            if data.startswith('{'):
                import json
                try:
                    payload = json.loads(data)
                    mode = payload.get("mode", "translation")
                    target = payload.get("target", "")
                    img_str = payload.get("image", "")
                    if ',' in img_str:
                        img_str = img_str.split(',')[1]
                    img_data = base64.b64decode(img_str)
                    nparr = np.frombuffer(img_data, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                except Exception:
                    continue
            else:
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
            pose_results = pose_landmarker.detect(mp_image)
            
            h, w, c = image.shape
            if pose_results.pose_landmarks:
                pose_lms = pose_results.pose_landmarks[0]
                CONNECTIONS = [
                    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
                    (11, 23), (12, 24), (23, 24), (23, 25), (25, 27),
                    (24, 26), (26, 28)
                ]
                for lm in pose_lms:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(image, (cx, cy), 4, (255, 0, 255), -1)
                for conn in CONNECTIONS:
                    p1 = pose_lms[conn[0]]
                    p2 = pose_lms[conn[1]]
                    x1, y1 = int(p1.x * w), int(p1.y * h)
                    x2, y2 = int(p2.x * w), int(p2.y * h)
                    cv2.line(image, (x1, y1), (x2, y2), (255, 255, 255), 2)
            
            features = []
            translation = "?"
            
            if results.hand_landmarks:
                if not hasattr(detector, 'histories'):
                    detector.histories = {'Left': [], 'Right': []}
                
                valid_hands = []
                
                for i, hand_landmarks in enumerate(results.hand_landmarks):
                    cat = results.handedness[i][0]
                    handedness = cat.category_name or cat.display_name
                    features = []
                    
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
                    
                    hist = detector.histories[handedness]
                    hist.append((current_wrist, current_index))
                    if len(hist) > 10:
                        hist.pop(0)
                        
                    wrist_dx, wrist_dy, index_dx, index_dy = 0.0, 0.0, 0.0, 0.0
                    if len(hist) == 10:
                        old_w, old_i = hist[0]
                        wrist_dx = current_wrist[0] - old_w[0]
                        wrist_dy = current_wrist[1] - old_w[1]
                        index_dx = current_index[0] - old_i[0]
                        index_dy = current_index[1] - old_i[1]
                        
                    features.extend([wrist_dx, wrist_dy, index_dx, index_dy])

                    hand_flag = 1.0 if handedness.strip().lower() == 'right' else -1.0
                    features.append(hand_flag)
                    
                    nose_offset_x, nose_offset_y = 0.0, 0.0
                    torso_offset_x, torso_offset_y = 0.0, 0.0
                    
                    if pose_results and pose_results.pose_landmarks:
                        pose_lms = pose_results.pose_landmarks[0]
                        nose = pose_lms[0]
                        l_shoulder, r_shoulder = pose_lms[11], pose_lms[12]
                        
                        torso_x = (l_shoulder.x + r_shoulder.x) / 2.0
                        torso_y = (l_shoulder.y + r_shoulder.y) / 2.0
                        
                        # Multiply by 10.0 to heavily weight spatial location in the KNN distance algorithm
                        nose_offset_x = (current_wrist[0] - nose.x) * 10.0
                        nose_offset_y = (current_wrist[1] - nose.y) * 10.0
                        torso_offset_x = (current_wrist[0] - torso_x) * 10.0
                        torso_offset_y = (current_wrist[1] - torso_y) * 10.0
                        
                    features.extend([nose_offset_x, nose_offset_y, torso_offset_x, torso_offset_y])

                    if len(features) == 51:
                        if not detector.is_hand(features):
                            cv2.putText(image, f"Object ignored ({handedness})", (50, 50 + i*40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        else:
                            valid_hands.append((hand_landmarks[0].x, features, hand_landmarks))
                            
                if valid_hands:
                    valid_hands.sort(key=lambda x: x[0])
                    
                    for _, _, hand_landmarks in valid_hands:
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
                            tx, ty = int(lm.x * w), int(lm.y * h)
                            cv2.circle(image, (tx, ty), 4, (0, 0, 255), -1)

                    combined_features = valid_hands[0][1].copy()
                    if len(valid_hands) > 1:
                        combined_features.extend(valid_hands[1][1])
                    else:
                        combined_features.extend([0.0] * 51)
                        
                    raw_translation = translator.predict(combined_features, mode=mode, target=target)
                else:
                    raw_translation = "?"
                
                prediction_buffer.append(raw_translation)
                if len(prediction_buffer) > 6:
                    prediction_buffer.pop(0)
                
                if len(prediction_buffer) == 6:
                    counts = {}
                    for p in prediction_buffer:
                        counts[p] = counts.get(p, 0) + 1
                    best_pred = max(counts, key=counts.get)
                    
                    if counts[best_pred] >= 4:
                        translation = best_pred
                    else:
                        translation = "?"
                else:
                    translation = "?"
            else:
                cv2.putText(image, "No skeleton located", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                prediction_buffer.clear()
                if hasattr(detector, 'histories'):
                    detector.histories['Left'].clear()
                    detector.histories['Right'].clear()

            # Macro and State Machine Logic
            spelling_out = ""
            import time
            now = time.time()
            
            # Check for macro timeouts and logic
            if mode == "translation" and macro_state == "FINGERSPELL_WAIT":
                if fingerspell_word and (now - last_letter_time) > 3.0:
                    # Commit the spelled word
                    translation = fingerspell_word
                    macro_state = "IDLE"
                    fingerspell_word = ""
                else:
                    spelling_out = fingerspell_word
                    
                    if translation != "?" and len(translation) == 1:
                        if not fingerspell_word or translation != fingerspell_word[-1]:
                            fingerspell_word += translation
                            last_letter_time = now
                            spelling_out = fingerspell_word
                    # intercept standard translation so UI doesn't speak letters
                    translation = "?"
                    
            elif mode == "translation" and translation != "?" and translation != last_spoken:
                # Normal translation processing
                last_translations.append((translation, now))
                # keep last 10 seconds
                last_translations = [t for t in last_translations if now - t[1] < 10.0]
                
                if len(last_translations) >= 2:
                    w1 = last_translations[-2][0]
                    w2 = last_translations[-1][0]
                    
                    if w1 == "HOW" and w2 == "YOU":
                        translation = "HOW ARE YOU"
                        last_translations.clear()
                    elif w1 == "MY" and w2 == "NAME":
                        translation = "MY NAME IS"
                        macro_state = "FINGERSPELL_WAIT"
                        fingerspell_word = ""
                        last_letter_time = now
                        last_translations.clear()

            # Update TTS and last_spoken state
            if translation and translation != "?":
                if translation != last_spoken:
                    try:
                        tts_queue.put(translation)
                    except NameError:
                        pass
                    last_spoken = translation
            else:
                if not results.hand_landmarks:
                    last_spoken = ""
                elif translation == "?":
                    last_spoken = ""
            
            _, buffer = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            b64_image = base64.b64encode(buffer).decode('utf-8')
            
            payload_out = {
                "image": b64_image,
                "translation": translation,
                "spelling": spelling_out,
                "skeleton_found": bool(results.hand_landmarks)
            }
            await websocket.send_json(payload_out)
            
    except WebSocketDisconnect:
        print("Client disconnected.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
