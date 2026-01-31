"""
Eye Tracking Game Controller for Dash Racing Game
Uses webcam to detect eye movements and control the game
"""

import cv2
import mediapipe as mp
import pyautogui
import time
import numpy as np

# PyAutoGUI settings for better control
pyautogui.PAUSE = 0.01  # Minimal pause between commands
pyautogui.FAILSAFE = False  # Disable failsafe to prevent interruption

class EyeTrackingController:
    def __init__(self):
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Eye landmarks indices
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]
        
        # Control thresholds (more sensitive)
        self.look_left_threshold = 0.45
        self.look_right_threshold = 0.55
        self.blink_threshold = 0.18
        self.blink_duration = 0.3
        
        # State tracking
        self.last_blink_time = 0
        self.last_action_time = 0
        self.game_started = False
        self.current_direction = None
        self.accelerating = False
        self.last_key_states = {'left': False, 'right': False, 'up': False}
        
        # Calibration
        self.calibrated = False
        self.center_position = 0.5
        
        # Debug mode
        self.debug = True
        
    def get_eye_aspect_ratio(self, eye_points, landmarks, frame_w, frame_h):
        """Calculate Eye Aspect Ratio (EAR) to detect blinks"""
        points = []
        for idx in eye_points:
            x = int(landmarks[idx].x * frame_w)
            y = int(landmarks[idx].y * frame_h)
            points.append([x, y])
        
        points = np.array(points)
        
        # Vertical distances
        A = np.linalg.norm(points[1] - points[5])
        B = np.linalg.norm(points[2] - points[4])
        
        # Horizontal distance
        C = np.linalg.norm(points[0] - points[3])
        
        # EAR formula
        ear = (A + B) / (2.0 * C)
        return ear
    
    def get_iris_position(self, iris_points, eye_points, landmarks, frame_w, frame_h):
        """Get normalized iris position (0 = left, 1 = right)"""
        # Get iris center
        iris_x = np.mean([landmarks[idx].x for idx in iris_points])
        
        # Get eye corners
        left_corner = landmarks[eye_points[0]].x
        right_corner = landmarks[eye_points[3]].x
        
        # Normalize position
        eye_width = right_corner - left_corner
        if eye_width == 0:
            return 0.5
        
        position = (iris_x - left_corner) / eye_width
        return position
    
    def calibrate(self, landmarks, frame_w, frame_h):
        """Calibrate center position"""
        left_pos = self.get_iris_position(self.LEFT_IRIS, self.LEFT_EYE, landmarks, frame_w, frame_h)
        right_pos = self.get_iris_position(self.RIGHT_IRIS, self.RIGHT_EYE, landmarks, frame_w, frame_h)
        self.center_position = (left_pos + right_pos) / 2
        self.calibrated = True
        print(f"✓ Calibrated! Center position: {self.center_position:.2f}")
    
    def process_frame(self, frame):
        """Process frame and detect eye movements"""
        frame_h, frame_w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return frame, None
        
        landmarks = results.multi_face_landmarks[0].landmark
        
        # Get eye metrics
        left_ear = self.get_eye_aspect_ratio(self.LEFT_EYE, landmarks, frame_w, frame_h)
        right_ear = self.get_eye_aspect_ratio(self.RIGHT_EYE, landmarks, frame_w, frame_h)
        avg_ear = (left_ear + right_ear) / 2
        
        # Get iris positions
        left_iris_pos = self.get_iris_position(self.LEFT_IRIS, self.LEFT_EYE, landmarks, frame_w, frame_h)
        right_iris_pos = self.get_iris_position(self.RIGHT_IRIS, self.RIGHT_EYE, landmarks, frame_w, frame_h)
        avg_iris_pos = (left_iris_pos + right_iris_pos) / 2
        
        # Calibration on first frame
        if not self.calibrated:
            self.calibrate(landmarks, frame_w, frame_h)
        
        # Detect actions
        action = self.detect_action(avg_ear, avg_iris_pos)
        
        # Draw visualization
        frame = self.draw_visualization(frame, avg_ear, avg_iris_pos, action)
        
        return frame, action
    
    def detect_action(self, ear, iris_pos):
        """Detect eye action and return control command"""
        current_time = time.time()
        action = {
            'direction': None,
            'accelerate': False,
            'blink': False,
            'start_game': False
        }
        
        # Detect blink (to start game or brake)
        if ear < self.blink_threshold:
            if current_time - self.last_blink_time > 1.0:
                self.last_blink_time = current_time
                action['blink'] = True
                
                if not self.game_started:
                    action['start_game'] = True
                    self.game_started = True
        
        # Detect horizontal eye movement (steering)
        if self.calibrated:
            if iris_pos < self.look_left_threshold:
                action['direction'] = 'left'
            elif iris_pos > self.look_right_threshold:
                action['direction'] = 'right'
            else:
                action['direction'] = 'center'
        
        # Always accelerate when game is running and eyes are open
        if self.game_started and ear > self.blink_threshold:
            action['accelerate'] = True
        
        return action
    
    def draw_visualization(self, frame, ear, iris_pos, action):
        """Draw overlay with eye tracking info"""
        h, w = frame.shape[:2]
        
        # Semi-transparent overlay
        overlay = frame.copy()
        
        # Status box
        cv2.rectangle(overlay, (10, 10), (300, 150), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        # Text info
        y_offset = 30
        cv2.putText(frame, "Eye Tracking Game Controller", (20, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        y_offset += 25
        status = "PLAYING" if self.game_started else "READY - Blink to Start"
        color = (0, 255, 0) if self.game_started else (0, 255, 255)
        cv2.putText(frame, f"Status: {status}", (20, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        y_offset += 25
        cv2.putText(frame, f"Eye Position: {iris_pos:.2f}", (20, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        y_offset += 25
        direction = action['direction'] if action else 'center'
        cv2.putText(frame, f"Direction: {direction.upper()}", (20, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        y_offset += 25
        accel_status = "ON" if action and action['accelerate'] else "OFF"
        cv2.putText(frame, f"Acceleration: {accel_status}", (20, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Direction indicator
        center_x = w // 2
        indicator_y = h - 50
        
        # Draw direction arrows
        if action and action['direction'] == 'left':
            cv2.arrowedLine(frame, (center_x, indicator_y), 
                          (center_x - 60, indicator_y), (0, 255, 255), 5)
        elif action and action['direction'] == 'right':
            cv2.arrowedLine(frame, (center_x, indicator_y), 
                          (center_x + 60, indicator_y), (0, 255, 255), 5)
        else:
            cv2.circle(frame, (center_x, indicator_y), 10, (0, 255, 0), -1)
        
        # Instructions
        cv2.putText(frame, "Look LEFT/RIGHT to steer | Blink to start | Press 'Q' to quit", 
                    (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def send_controls(self, action):
        """Send keyboard commands to control the game"""
        if not action:
            return
        
        current_time = time.time()
        
        # Throttle updates slightly to avoid spam
        if current_time - self.last_action_time < 0.05:
            return
        
        self.last_action_time = current_time
        
        # Start game with explicit key press
        if action['start_game']:
            print("🎮 Starting game - Pressing 'C'...")
            pyautogui.press('c', interval=0.1)
            time.sleep(0.3)
            return
        
        # Handle steering
        new_left = action['direction'] == 'left'
        new_right = action['direction'] == 'right'
        
        # Left arrow
        if new_left != self.last_key_states['left']:
            if new_left:
                pyautogui.keyDown('left')
                if self.debug:
                    print("⬅️ Steering LEFT")
            else:
                pyautogui.keyUp('left')
            self.last_key_states['left'] = new_left
        
        # Right arrow
        if new_right != self.last_key_states['right']:
            if new_right:
                pyautogui.keyDown('right')
                if self.debug:
                    print("➡️ Steering RIGHT")
            else:
                pyautogui.keyUp('right')
            self.last_key_states['right'] = new_right
        
        # Handle acceleration
        new_up = action['accelerate']
        if new_up != self.last_key_states['up']:
            if new_up:
                pyautogui.keyDown('up')
                if self.debug:
                    print("⬆️ ACCELERATING")
            else:
                pyautogui.keyUp('up')
                if self.debug:
                    print("⏸️ Stopped accelerating")
            self.last_key_states['up'] = new_up
    
    def cleanup(self):
        """Release all keys"""
        print("\n🛑 Releasing all keys...")
        pyautogui.keyUp('left')
        pyautogui.keyUp('right')
        pyautogui.keyUp('up')
        pyautogui.keyUp('down')
        self.last_key_states = {'left': False, 'right': False, 'up': False}
    
    def run(self):
        """Main loop"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Error: Could not open webcam")
            return
        
        print("=" * 60)
        print("🎮 Eye Tracking Game Controller Started!")
        print("=" * 60)
        print("\nInstructions:")
        print("1. Look at the center of the screen to calibrate")
        print("2. BLINK to start the game (press 'C')")
        print("3. Look LEFT or RIGHT to steer")
        print("4. Keep eyes open to accelerate")
        print("5. Press 'Q' to quit\n")
        print("⚠️  IMPORTANT:")
        print("   - Click on the GAME WINDOW in your browser")
        print("   - Make sure it has FOCUS (click on it)")
        print("   - The game window must be active to receive controls")
        print("=" * 60)
        print("\n🎥 Starting webcam...")
        
        time.sleep(2)  # Give user time to focus the game window
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Process frame
                frame, action = self.process_frame(frame)
                
                # Send controls
                self.send_controls(action)
                
                # Display
                cv2.imshow('Eye Tracking Controller', frame)
                
                # Exit on 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            print("\n⚠ Interrupted by user")
        
        finally:
            self.cleanup()
            cap.release()
            cv2.destroyAllWindows()
            print("\n✓ Eye tracking controller stopped")

def main():
    controller = EyeTrackingController()
    controller.run()

if __name__ == "__main__":
    main()
