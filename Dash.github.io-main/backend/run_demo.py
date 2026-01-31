"""
Run the game and eye tracker side-by-side for demonstration
"""
import cv2
import mediapipe as mp
import pyautogui
import time
import numpy as np
import webbrowser
import os
import subprocess

# PyAutoGUI settings for better control
pyautogui.PAUSE = 0.01
pyautogui.FAILSAFE = False

class EyeTrackingDemo:
    def __init__(self):
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Eye landmarks indices
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]
        
        # Control thresholds (more sensitive)
        self.look_left_threshold = 0.45
        self.look_right_threshold = 0.55
        self.blink_threshold = 0.18
        
        # State tracking
        self.last_blink_time = 0
        self.last_action_time = 0
        self.game_started = False
        self.last_key_states = {'left': False, 'right': False, 'up': False}
        
        # Calibration
        self.calibrated = False
        self.center_position = 0.5
    
    def get_eye_aspect_ratio(self, eye_points, landmarks, frame_w, frame_h):
        """Calculate Eye Aspect Ratio (EAR) to detect blinks"""
        points = []
        for idx in eye_points:
            x = int(landmarks[idx].x * frame_w)
            y = int(landmarks[idx].y * frame_h)
            points.append([x, y])
        
        points = np.array(points)
        A = np.linalg.norm(points[1] - points[5])
        B = np.linalg.norm(points[2] - points[4])
        C = np.linalg.norm(points[0] - points[3])
        
        ear = (A + B) / (2.0 * C)
        return ear
    
    def get_iris_position(self, iris_points, eye_points, landmarks, frame_w, frame_h):
        """Get normalized iris position (0 = left, 1 = right)"""
        iris_x = np.mean([landmarks[idx].x for idx in iris_points])
        left_corner = landmarks[eye_points[0]].x
        right_corner = landmarks[eye_points[3]].x
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
    
    def detect_action(self, ear, iris_pos):
        """Detect eye action and return control command"""
        current_time = time.time()
        action = {
            'direction': None,
            'accelerate': False,
            'blink': False,
            'start_game': False
        }
        
        # Detect blink
        if ear < self.blink_threshold:
            if current_time - self.last_blink_time > 1.0:
                self.last_blink_time = current_time
                action['blink'] = True
                
                if not self.game_started:
                    action['start_game'] = True
                    self.game_started = True
        
        # Detect horizontal eye movement
        if self.calibrated:
            if iris_pos < self.look_left_threshold:
                action['direction'] = 'left'
            elif iris_pos > self.look_right_threshold:
                action['direction'] = 'right'
            else:
                action['direction'] = 'center'
        
        # Auto-accelerate when eyes open and game started
        if self.game_started and ear > self.blink_threshold:
            action['accelerate'] = True
        
        return action
    
    def draw_visualization(self, frame, ear, iris_pos, action):
        """Draw large, clear overlay for demonstration"""
        h, w = frame.shape[:2]
        
        # Draw face mesh for visual effect
        overlay = frame.copy()
        
        # Large status indicator at top
        status_h = 120
        cv2.rectangle(overlay, (0, 0), (w, status_h), (20, 20, 20), -1)
        frame = cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)
        
        # Title
        cv2.putText(frame, "EYE TRACKING GAME CONTROL", (20, 40), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 255), 3)
        
        # Game status
        if self.game_started:
            status_text = "GAME ACTIVE"
            status_color = (0, 255, 0)
        else:
            status_text = "BLINK TO START"
            status_color = (0, 200, 255)
        
        cv2.putText(frame, status_text, (20, 85), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, status_color, 2)
        
        # Bottom control panel
        panel_y = h - 200
        cv2.rectangle(overlay, (0, panel_y), (w, h), (20, 20, 20), -1)
        frame = cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)
        
        # Direction indicator - BIG and CLEAR
        center_x = w // 2
        indicator_y = panel_y + 60
        
        if action:
            # Draw current direction with large arrows
            if action['direction'] == 'left':
                # Left arrow
                cv2.arrowedLine(frame, (center_x + 50, indicator_y), 
                              (center_x - 100, indicator_y), (0, 255, 255), 15, tipLength=0.3)
                cv2.putText(frame, "STEERING LEFT", (center_x - 200, indicator_y + 60), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 255), 2)
                
            elif action['direction'] == 'right':
                # Right arrow
                cv2.arrowedLine(frame, (center_x - 50, indicator_y), 
                              (center_x + 100, indicator_y), (0, 255, 255), 15, tipLength=0.3)
                cv2.putText(frame, "STEERING RIGHT", (center_x - 10, indicator_y + 60), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 255), 2)
            else:
                # Center
                cv2.circle(frame, (center_x, indicator_y), 25, (0, 255, 0), -1)
                cv2.putText(frame, "STRAIGHT", (center_x - 80, indicator_y + 60), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
            
            # Acceleration indicator
            accel_x = w - 200
            if action['accelerate']:
                cv2.putText(frame, "ACCELERATING", (accel_x - 100, panel_y + 140), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)
                cv2.arrowedLine(frame, (accel_x, panel_y + 160), 
                              (accel_x, panel_y + 100), (0, 255, 0), 8, tipLength=0.4)
        
        # Eye position bar
        bar_y = panel_y + 30
        bar_w = w - 40
        cv2.rectangle(frame, (20, bar_y - 5), (20 + bar_w, bar_y + 5), (100, 100, 100), -1)
        
        # Current position marker
        marker_x = int(20 + iris_pos * bar_w)
        marker_color = (0, 255, 255) if action and action['direction'] != 'center' else (0, 255, 0)
        cv2.circle(frame, (marker_x, bar_y), 12, marker_color, -1)
        
        # Thresholds
        left_thresh_x = int(20 + self.look_left_threshold * bar_w)
        right_thresh_x = int(20 + self.look_right_threshold * bar_w)
        cv2.line(frame, (left_thresh_x, bar_y - 15), (left_thresh_x, bar_y + 15), (255, 100, 100), 3)
        cv2.line(frame, (right_thresh_x, bar_y - 15), (right_thresh_x, bar_y + 15), (255, 100, 100), 3)
        
        return frame
    
    def send_controls(self, action):
        """Send keyboard commands"""
        if not action:
            return
        
        current_time = time.time()
        if current_time - self.last_action_time < 0.05:
            return
        self.last_action_time = current_time
        
        # Start game
        if action['start_game']:
            pyautogui.press('c', interval=0.1)
            time.sleep(0.3)
            return
        
        # Steering
        new_left = action['direction'] == 'left'
        new_right = action['direction'] == 'right'
        
        if new_left != self.last_key_states['left']:
            if new_left:
                pyautogui.keyDown('left')
            else:
                pyautogui.keyUp('left')
            self.last_key_states['left'] = new_left
        
        if new_right != self.last_key_states['right']:
            if new_right:
                pyautogui.keyDown('right')
            else:
                pyautogui.keyUp('right')
            self.last_key_states['right'] = new_right
        
        # Acceleration
        new_up = action['accelerate']
        if new_up != self.last_key_states['up']:
            if new_up:
                pyautogui.keyDown('up')
            else:
                pyautogui.keyUp('up')
            self.last_key_states['up'] = new_up
    
    def cleanup(self):
        """Release all keys"""
        pyautogui.keyUp('left')
        pyautogui.keyUp('right')
        pyautogui.keyUp('up')
        pyautogui.keyUp('down')
    
    def run(self):
        """Main loop with side-by-side display"""
        # Open game in browser
        game_path = os.path.abspath("index.html")
        print("🎮 Opening game in browser...")
        webbrowser.open('file://' + game_path)
        
        time.sleep(3)  # Wait for browser to open
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Error: Could not open webcam")
            return
        
        # Set camera resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        print("\n" + "=" * 70)
        print("🎥 EYE TRACKING DEMO - SIDE BY SIDE VIEW")
        print("=" * 70)
        print("\n📍 SETUP:")
        print("   1. Position the webcam window on the RIGHT side")
        print("   2. Position the game browser on the LEFT side")
        print("   3. Click on the GAME to give it focus")
        print("\n🎮 CONTROLS:")
        print("   👀 Look LEFT/RIGHT → Steer car")
        print("   😑 BLINK → Start game")
        print("   👁️  Eyes OPEN → Auto-accelerate")
        print("   ⌨️  Press 'Q' → Quit demo")
        print("\n✨ Starting in 3 seconds...")
        print("=" * 70 + "\n")
        
        time.sleep(3)
        
        # Create named window and position it
        cv2.namedWindow('Eye Tracking Demo', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Eye Tracking Demo', 1000, 600)
        cv2.moveWindow('Eye Tracking Demo', 900, 100)  # Position on right side
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Flip for mirror effect
                frame = cv2.flip(frame, 1)
                frame_h, frame_w = frame.shape[:2]
                
                # Process frame
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(rgb_frame)
                
                if results.multi_face_landmarks:
                    landmarks = results.multi_face_landmarks[0].landmark
                    
                    # Get metrics
                    left_ear = self.get_eye_aspect_ratio(self.LEFT_EYE, landmarks, frame_w, frame_h)
                    right_ear = self.get_eye_aspect_ratio(self.RIGHT_EYE, landmarks, frame_w, frame_h)
                    avg_ear = (left_ear + right_ear) / 2
                    
                    left_iris = self.get_iris_position(self.LEFT_IRIS, self.LEFT_EYE, landmarks, frame_w, frame_h)
                    right_iris = self.get_iris_position(self.RIGHT_IRIS, self.RIGHT_EYE, landmarks, frame_w, frame_h)
                    avg_iris = (left_iris + right_iris) / 2
                    
                    # Calibrate on first detection
                    if not self.calibrated:
                        self.calibrate(landmarks, frame_w, frame_h)
                    
                    # Detect action
                    action = self.detect_action(avg_ear, avg_iris)
                    
                    # Draw visualization
                    frame = self.draw_visualization(frame, avg_ear, avg_iris, action)
                    
                    # Send controls
                    self.send_controls(action)
                
                # Display
                cv2.imshow('Eye Tracking Demo', frame)
                
                # Exit on 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            print("\n⚠ Demo stopped by user")
        
        finally:
            self.cleanup()
            cap.release()
            cv2.destroyAllWindows()
            print("\n✅ Demo ended successfully!")

def main():
    demo = EyeTrackingDemo()
    demo.run()

if __name__ == "__main__":
    main()
