import os
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from keras_facenet import FaceNet

import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

import sys

class_name = sys.argv[1] if len(sys.argv) > 1 else "General"
class_time_str = sys.argv[2] if len(sys.argv) > 2 else ""

KNOWN_FACES_DIR = "known_faces"
ATTENDANCE_FILE = f"attendance_{class_name}.xlsx"
CAPTURES_DIR = "attendance_captures"

os.makedirs(CAPTURES_DIR, exist_ok=True)

print("Loading Keras FaceNet model (with internal MTCNN)...")
embedder = FaceNet()

print("Computing known face embeddings...")
known_embeddings = {}
marked_students = set()

if os.path.exists(KNOWN_FACES_DIR):
    for file in os.listdir(KNOWN_FACES_DIR):
        path = os.path.join(KNOWN_FACES_DIR, file)
        
        if file.startswith('.'):
            continue
            
        name = os.path.splitext(file)[0]

        img = cv2.imread(path)
        if img is None:
            continue
            
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # .extract() automatically uses MTCNN, aligns the face, and computes the embedding perfectly!
        detections = embedder.extract(img_rgb, threshold=0.90)
        
        if detections:
            # Assuming the primary face is the first one found
            embedding = detections[0]['embedding']
            known_embeddings[name] = embedding
        else:
            print(f"Could not automatically extract face from {file}")
else:
    print(f"Warning: Directory '{KNOWN_FACES_DIR}' not found! Creating it...")
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

print("Embeddings loaded successfully!")

def init_attendance(known_names):
    today = datetime.now().strftime("%Y-%m-%d")
    columns = ["Date", "Name", "Time", "Status"]
    
    try:
        df = pd.read_excel(ATTENDANCE_FILE, engine="openpyxl")
    except:
        df = pd.DataFrame(columns=columns)
        
    # Backward compatibility
    if "Date" not in df.columns:
        df["Date"] = today
    if "Status" not in df.columns:
        df["Status"] = "Absent"
        
    # Ensure today's entries exist for all known faces
    today_data = df[df["Date"] == today]
    missing_names = [n for n in known_names if n not in today_data["Name"].values]
    
    if missing_names:
        new_rows = pd.DataFrame([[today, n, "", "Absent"] for n in missing_names], columns=columns)
        df = pd.concat([df, new_rows], ignore_index=True)
        
    df.to_excel(ATTENDANCE_FILE, index=False)

init_attendance(list(known_embeddings.keys()))

def mark_attendance(name):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    time_string = now.strftime("%H:%M:%S")

    status = "Present"
    if class_time_str:
        try:
            class_time_obj = datetime.strptime(f"{today} {class_time_str}", "%Y-%m-%d %H:%M")
            time_diff = now - class_time_obj
            if time_diff.total_seconds() > 20 * 60:
                status = "Late"
        except Exception as e:
            print(f"Error parsing class time: {e}")

    try:
        df = pd.read_excel(ATTENDANCE_FILE, engine="openpyxl")
        mask = (df["Date"] == today) & (df["Name"] == name)
        
        if mask.any():
            idx = df.index[mask].tolist()[0]
            if df.at[idx, "Status"] not in ["Present", "Late"]:
                df.at[idx, "Time"] = time_string
                df.at[idx, "Status"] = status
                df.to_excel(ATTENDANCE_FILE, index=False)
                print(f"{name} marked {status} in Excel!")
        else:
            new_entry = pd.DataFrame([[today, name, time_string, status]], columns=["Date", "Name", "Time", "Status"])
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_excel(ATTENDANCE_FILE, index=False)
            print(f"{name} marked {status} in Excel!")
    except Exception as e:
        print(f"Error marking attendance: {e}")

def recognize_faces():
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

    if not cap.isOpened():
        print("Camera could not be opened.")
        return

    print("Press 'q' or close the window to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            detections = embedder.extract(img_rgb, threshold=0.90)

            for face in detections:
                box = face['box']
                x, y, w, h = box
                embedding = face['embedding']

                best_match_name = "Unknown"
                best_distance = float('inf')

                for name, known_embedding in known_embeddings.items():
                    distance = np.linalg.norm(embedding - known_embedding)
                    if distance < best_distance:
                        best_distance = distance
                        best_match_name = name

                # DeepFace uses a FaceNet L2 threshold around 1.0 - 1.04.
                # A mathematical distance of 0.8 is a strong match but corresponds to 68% raw cosine similarity.
                # We map the distance to a more intuitive 0-100% confidence scale where <=0.90 gives >=80%.
                if best_distance <= 0.90:
                    accuracy = 100.0 - (best_distance / 0.90) * 20.0
                else:
                    accuracy = max(0.0, 80.0 - ((best_distance - 0.90) / 0.60) * 80.0)

                if best_distance < 0.90:
                    if best_match_name not in marked_students and best_match_name != "Unknown":
                        mark_attendance(best_match_name)
                        marked_students.add(best_match_name)
                        
                        if accuracy > 80:
                            save_path = os.path.join(CAPTURES_DIR, f"{best_match_name}_{datetime.now().strftime('%H-%M-%S')}.jpg")
                            cv2.imwrite(save_path, frame)
                            print(f"Captured high-accuracy ({accuracy:.1f}%) image for {best_match_name} at {save_path}")
                            
                    display_name = f"{best_match_name} ({accuracy:.1f}%)"
                else:
                    display_name = "Unknown"

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                cv2.putText(frame, display_name, (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.9, (0,255,0), 2)

        except Exception as e:
            print(f"Error processing frame: {e}")

        cv2.imshow("Real-Time Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty("Real-Time Attendance", cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    recognize_faces()
