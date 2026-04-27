import asyncio
import cv2
import mediapipe as mp

import numpy as np
import csv
import os
from sklearn.neighbors import KNeighborsClassifier
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandDetector:
    def __init__(self):
        self.knn = KNeighborsClassifier(n_neighbors=3)
        self.is_trained = False

    def train_model(self, csv_filepath):
        if not os.path.exists(csv_filepath) or os.stat(csv_filepath).st_size == 0:
            self.is_trained = False
            return False
        
        X = []
        y = []
        with open(csv_filepath, 'r') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) < 43: continue # 1 label + at least 42 features
                feats = [float(x) if x.strip() != '' else 0.0 for x in row[1:]]
                if len(feats) == 42:
                    feats.extend([0.0, 0.0, 0.0, 0.0]) # Pad 4 motion features
                if len(feats) == 46:
                    feats.extend([0.0, 0.0, 0.0, 0.0, 0.0]) # Pad 5 pose features
                if len(feats) >= 51:
                    X.append(feats[:51])
                    y.append(row[0])
                
        if len(X) == 0:
            self.is_trained = False
            return False
            
        n_samples = len(X)
        self.knn.n_neighbors = min(3, n_samples)
        self.knn.fit(X, y)
        self.is_trained = True
        return True

    def is_hand(self, features):
        if not self.is_trained:
            return True
        pred = self.knn.predict([features])
        return pred[0] == '1'

class ASLClassifier:
    def __init__(self):
        self.knn = KNeighborsClassifier(n_neighbors=3)
        self.is_trained = False

    def train_model(self, csv_filepath):
        if not os.path.exists(csv_filepath) or os.stat(csv_filepath).st_size == 0:
            self.is_trained = False
            return False
            
        X = []
        y = []
        with open(csv_filepath, 'r') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) < 43: continue 
                feats = [float(x) if x.strip() != '' else 0.0 for x in row[1:]]
                if len(feats) == 42:
                    feats.extend([0.0, 0.0, 0.0, 0.0]) # Pad 4 motion features
                if len(feats) == 46:
                    feats.extend([0.0, 0.0, 0.0, 0.0, 0.0]) # Pad 5 pose features
                if len(feats) >= 51:
                    X.append(feats[:51])
                    y.append(row[0])
                
        if len(X) == 0:
            self.is_trained = False
            return False
            
        n_samples = len(X)
        self.knn.n_neighbors = min(3, n_samples)
        self.knn.fit(X, y)
        self.is_trained = True
        return True

    def predict(self, features):
        if not self.is_trained:
            return '?'
        pred = self.knn.predict([features])
        return pred[0]

def log_data(filepath, label, features):
    file_exists = os.path.exists(filepath)
    try:
        with open(filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists or os.stat(filepath).st_size == 0:
                header = ['Label'] + [f'Feature{i}' for i in range(len(features))]
                writer.writerow(header)
            writer.writerow([label] + features)
        print(f"Logged {label} to {filepath}")
        return True
    except PermissionError:
        print(f"Permission Denied: Could not save data. Please close {filepath} in Excel or any other program!")
        return False

def main():
    detector = HandDetector()
    translator = ASLClassifier()

    if not translator.train_model("asl_data_real.csv"):
        print("Could not train ASL model yet. Add data.")
    detector.train_model("hand_detection_data.csv")

    # Initialize Modern MediaPipe Task Vision HandLandmarker
    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=2)
    landmarker = vision.HandLandmarker.create_from_options(options)

    pose_url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    import urllib.request
    if not os.path.exists("pose_landmarker.task"):
        print("Downloading pose model...")
        urllib.request.urlretrieve(pose_url, "pose_landmarker.task")

    base_options_pose = python.BaseOptions(model_asset_path='pose_landmarker.task')
    options_pose = vision.PoseLandmarkerOptions(base_options=base_options_pose)
    pose_landmarker = vision.PoseLandmarker.create_from_options(options_pose)

    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break
            
        image = cv2.flip(image, 1)
        # MediaPipe expects RGB
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
        
        primary_features = []
        
        if results.hand_landmarks:
            if not hasattr(detector, 'histories'):
                detector.histories = {'Left': [], 'Right': []}
                
            for i, hand_landmarks in enumerate(results.hand_landmarks):
                cat = results.handedness[i][0]
                handedness = cat.category_name or cat.display_name
                features = []
                
                # Get bounding box to create scale-invariant relative features
                h, w, c = image.shape
                x_max = 0
                y_max = 0
                x_min = w
                y_min = h
                
                for lm in hand_landmarks:
                    x, y = int(lm.x * w), int(lm.y * h)
                    if x > x_max: x_max = x
                    if x < x_min: x_min = x
                    if y > y_max: y_max = y
                    if y < y_min: y_min = y
                
                box_w = x_max - x_min
                box_h = y_max - y_min
                box_w = box_w if box_w > 0 else 1
                box_h = box_h if box_h > 0 else 1
                
                # Extract 42 geometric (x,y) features relative to the bounding box
                for lm in hand_landmarks:
                    rel_x = (lm.x * w - x_min) / box_w
                    rel_y = (lm.y * h - y_min) / box_h
                    features.extend([rel_x, rel_y])

                # Extract 4 motion features (dx, dy of wrist and index over 10 frames)
                current_wrist = (hand_landmarks[0].x, hand_landmarks[0].y)
                current_index = (hand_landmarks[8].x, hand_landmarks[8].y)
                
                hist = detector.histories[handedness]
                hist.append((current_wrist, current_index))
                if len(hist) > 10:
                    hist.pop(0)
                    
                wrist_dx, wrist_dy, index_dx, index_dy = 0.0, 0.0, 0.0, 0.0
                if len(hist) == 10:
                    old_wrist, old_index = hist[0]
                    wrist_dx = current_wrist[0] - old_wrist[0]
                    wrist_dy = current_wrist[1] - old_wrist[1]
                    index_dx = current_index[0] - old_index[0]
                    index_dy = current_index[1] - old_index[1]
                    
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
                    if not primary_features:
                        primary_features = features
                        
                    if not detector.is_hand(features):
                        cv2.putText(image, f"Object ignored ({handedness})", (50, 50 + i*40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    else:
                        # Draw the skeleton perfectly manually!
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
                        
                        translated = translator.predict(features)
                        if translated != '?':
                            wx, wy = int(hand_landmarks[0].x * w), int(hand_landmarks[0].y * h)
                            cv2.putText(image, translated, (max(wx - 20, 10), max(wy + 40, 10)), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

                        # Movement text
                        movement_magnitude = (wrist_dx**2 + wrist_dy**2)**0.5
                        if movement_magnitude > 0.02:
                            wx, wy = int(hand_landmarks[0].x * w), int(hand_landmarks[0].y * h)
                            cv2.putText(image, "Motion", (max(wx + 20, 10), max(wy + 40, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 100, 100), 2)
        else:
            cv2.putText(image, "No skeleton located", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            if hasattr(detector, 'histories'):
                detector.histories['Left'].clear()
                detector.histories['Right'].clear()

        cv2.putText(image, "A-Z for Letters | SPACE for Word", (10, image.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.imshow('Live ASL Translator Python', image)
        
        key = cv2.waitKey(5) & 0xFF
        if key == 27:
            break
            #logging data for ASL letters (A-Z) and words (SPACEBAR)
        if len(primary_features) == 51:
            if 97 <= key <= 122 or 65 <= key <= 90: # a-z or A-Z
                label = chr(key).upper()
                if log_data("asl_data_real.csv", label, features):
                    translator.train_model("asl_data_real.csv")
            elif key == 32: # SPACEBAR
                import tkinter as tk
                from tkinter import simpledialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                word_label = simpledialog.askstring("Log ASL Word", "CAMERA PAUSED.\nEnter Word Label (e.g. HELLO):", parent=root)
                root.destroy()
                
                if word_label and word_label.strip():
                    word_label = word_label.strip().upper()
                    if log_data("asl_data_real.csv", word_label, features):
                        translator.train_model("asl_data_real.csv")
                        print(f"Logged word '{word_label}'. Resuming camera...")
                else:
                    print("No word entered. Resuming camera...")
            elif key == 48 or key == 49: # '0' or '1'
                char_key = chr(key)
                if log_data("hand_detection_data.csv", char_key, features):
                    detector.train_model("hand_detection_data.csv")
                
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
