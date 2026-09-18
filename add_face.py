import os
import cv2
import sys

KNOWN_FACES_DIR = "known_faces"

def add_new_face():
    if len(sys.argv) > 1:
        name = sys.argv[1].strip()
    else:
        name = input("Enter the name of the person: ").strip()
        
    if not name:
        print("Name cannot be empty.")
        return

    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    save_path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")

    if os.path.exists(save_path):
        print(f"Warning: A face data for '{name}' already exists. Overwriting...")

    # Open the default camera
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("\n" + "="*50)
    print(f"Adding face for: {name}")
    print("Look at the camera and press 'SPACE' or 'c' to capture.")
    print("Press 'q' to cancel.")
    print("="*50 + "\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read from camera.")
            break

        # Display instructions on screen
        display_frame = frame.copy()
        cv2.putText(display_frame, f"Capturing: {name}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(display_frame, "Press SPACE to capture, Q to quit", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        cv2.imshow("Capture New Face", display_frame)

        key = cv2.waitKey(1) & 0xFF
        
        # Check window close
        if cv2.getWindowProperty("Capture New Face", cv2.WND_PROP_VISIBLE) < 1:
            break
            
        if key == ord('q'):
            print("Cancelled.")
            break
        elif key == ord(' ') or key == ord('c'):
            # Save the clean frame (without written instructions)
            cv2.imwrite(save_path, frame)
            print(f"\nSuccess! Successfully saved face data for {name} at {save_path}")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    add_new_face()
