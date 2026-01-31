"""
WebSocket server for eye tracking that sends data directly to the game
Enhanced with Kalman filter smoothing, velocity scaling, and professional calibration
"""
import cv2
import mediapipe as mp
import numpy as np
import asyncio
import websockets
import json
import threading
import webbrowser
import os
import time
from collections import deque

class KalmanFilter1D:
    """Simple 1D Kalman Filter for smooth cursor tracking"""
    def __init__(self, process_variance, measurement_variance, initial_value=0, initial_estimate_error=1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimate = initial_value
        self.estimate_error = initial_estimate_error
        self.kalman_gain = 0
        
    def update(self, measurement):
        # Predict
        prior_estimate = self.estimate
        prior_estimate_error = self.estimate_error + self.process_variance
        
        # Update
        self.kalman_gain = prior_estimate_error / (prior_estimate_error + self.measurement_variance)
        self.estimate = prior_estimate + self.kalman_gain * (measurement - prior_estimate)
        self.estimate_error = (1 - self.kalman_gain) * prior_estimate_error
        
        return self.estimate

class EyeTrackingServer:
    def __init__(self):
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Eye landmarks
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]
        
        # Thresholds (improved sensitivity for responsive turning)
        self.look_left_threshold = 0.40
        self.look_right_threshold = 0.60
        self.blink_threshold = 0.12  # INCREASED from 0.18 - less sensitive to unwanted blinks
        self.wink_threshold = 0.10  # INCREASED from 0.15 - requires more pronounced wink
        self.eyes_closed_threshold = 0.15  # INCREASED from 0.20 - requires more closure
        self.eyes_closed_duration = 0.5    # INCREASED from 0.3 - eyes must be closed longer
        
        # Advanced smoothing - Kalman filters for X and Y
        self.kalman_x = KalmanFilter1D(process_variance=0.0001, measurement_variance=0.001, initial_value=0.5)
        self.kalman_y = KalmanFilter1D(process_variance=0.0001, measurement_variance=0.001, initial_value=0.5)
        
        # Moving average for additional smoothing
        self.smooth_window_size = 3
        self.cursor_x_history = deque(maxlen=self.smooth_window_size)
        self.cursor_y_history = deque(maxlen=self.smooth_window_size)
        
        # Cursor sensitivity and control parameters
        self.cursor_sensitivity = 1.0  # Direct 1:1 mapping for full screen
        self.dead_zone_radius = 0.05  # 5% dead zone around center to avoid shaking
        self.velocity_scale_min = 0.5  # Slow down small movements
        self.velocity_scale_max = 1.5  # Speed up large movements
        self.max_velocity = 0.15  # Maximum change per frame
        
        # Calibration system
        self.calibrated = False
        self.calibration_mode = False
        self.calibration_points = {
            'center': None,
            'top_left': None,
            'top_right': None,
            'bottom_left': None,
            'bottom_right': None
        }
        self.calibration_step = 0
        self.calibration_samples = []  # Collect multiple samples for each point
        self.sample_count = 0
        self.samples_per_point = 30  # Collect 30 frames per calibration point
        
        # Center and corner position mapping
        self.center_position = 0.5
        self.center_y_position = 0.5
        self.game_started = False
        self.last_blink_time = 0
        self.eyes_closed_start = None  # Track when eyes were closed
        
        # Smoothing for reducing latency/jitter
        self.direction_history = []
        self.history_size = 3  # Increased for smoother movement
        
        # Cursor position tracking
        self.last_cursor_x = 0.5
        self.last_cursor_y = 0.5
        self.last_raw_x = 0.5
        self.last_raw_y = 0.5
        
        # Head/face position tracking
        self.last_nose_x = None
        self.last_nose_y = None
        
        # WebSocket clients
        self.clients = set()
        
        # Head/face position tracking
        self.last_nose_x = None
        self.last_nose_y = None
        
        # WebSocket clients
        self.clients = set()
        
    def get_eye_aspect_ratio(self, eye_points, landmarks, frame_w, frame_h):
        points = []
        for idx in eye_points:
            x = int(landmarks[idx].x * frame_w)
            y = int(landmarks[idx].y * frame_h)
            points.append([x, y])
        
        points = np.array(points)
        A = np.linalg.norm(points[1] - points[5])
        B = np.linalg.norm(points[2] - points[4])
        C = np.linalg.norm(points[0] - points[3])
        
        return (A + B) / (2.0 * C)
    
    def get_iris_position(self, iris_points, eye_points, landmarks, frame_w, frame_h, is_left_eye=True):
        iris_x = np.mean([landmarks[idx].x for idx in iris_points])
        iris_y = np.mean([landmarks[idx].y for idx in iris_points])
        
        # Get the two horizontal corners of the eye
        point0_x = landmarks[eye_points[0]].x
        point3_x = landmarks[eye_points[3]].x
        
        # Ensure consistent left-to-right ordering
        left_corner = min(point0_x, point3_x)
        right_corner = max(point0_x, point3_x)
        
        eye_width = right_corner - left_corner
        
        if eye_width == 0:
            return 0.5, iris_y
        
        # Calculate position within eye: 0 = left gaze, 1 = right gaze
        # Normalize iris position to 0-1 range where 0=looking left, 1=looking right
        iris_pos = (iris_x - left_corner) / eye_width
        
        # EXTENDED RANGE: Allow slight extrapolation beyond eye boundaries
        # This lets users reach the full screen when looking all the way to the sides
        # Allow up to 15% beyond the eye boundaries on each side
        iris_pos = np.clip(iris_pos, -0.15, 1.15)
        
        # Now map the extended range (-0.15 to 1.15) to full screen (0.0 to 1.0)
        # This gives full screen movement while maintaining a dead zone outside the eye
        iris_pos = (iris_pos + 0.15) / 1.30  # Normalize: (-0.15->0.0, 0.0->0.115, 0.5->0.5, 1.0->0.885, 1.15->1.0)
        iris_pos = np.clip(iris_pos, 0.0, 1.0)  # Final clamp to valid range
        
        return iris_pos, iris_y
    
    def calibrate(self, landmarks, frame_w, frame_h):
        left_pos, left_y = self.get_iris_position(self.LEFT_IRIS, self.LEFT_EYE, landmarks, frame_w, frame_h, is_left_eye=True)
        right_pos, right_y = self.get_iris_position(self.RIGHT_IRIS, self.RIGHT_EYE, landmarks, frame_w, frame_h, is_left_eye=False)
        self.center_position = (left_pos + right_pos) / 2
        self.center_y_position = (left_y + right_y) / 2
        # Initialize nose position for head tracking
        self.last_nose_x = landmarks[1].x  # Nose tip
        self.last_nose_y = landmarks[1].y
        self.calibrated = True
        print(f"✓ Calibrated! Center X: {self.center_position:.2f}, Y: {self.center_y_position:.2f}")
    
    def smooth_cursor_position(self, raw_x, raw_y):
        """Apply Kalman filtering and moving average smoothing for professional cursor tracking"""
        
        # Apply Kalman filter first (removes noise)
        filtered_x = self.kalman_x.update(raw_x)
        filtered_y = self.kalman_y.update(raw_y)
        
        # Apply moving average smoothing
        self.cursor_x_history.append(filtered_x)
        self.cursor_y_history.append(filtered_y)
        
        smooth_x = np.mean(list(self.cursor_x_history))
        smooth_y = np.mean(list(self.cursor_y_history))
        
        # Apply velocity scaling (adaptive speed based on movement magnitude)
        delta_x = abs(smooth_x - self.last_cursor_x)
        delta_y = abs(smooth_y - self.last_cursor_y)
        velocity = np.sqrt(delta_x**2 + delta_y**2)
        
        # Scale velocity: slow for small movements, fast for large ones
        if velocity < 0.01:
            velocity_scale = self.velocity_scale_min  # Slow down tiny movements
        elif velocity > 0.1:
            velocity_scale = self.velocity_scale_max  # Speed up large movements
        else:
            # Linear interpolation between min and max
            velocity_scale = self.velocity_scale_min + (velocity / 0.1) * (self.velocity_scale_max - self.velocity_scale_min)
        
        # Apply velocity scaling
        scaled_x = self.last_cursor_x + (smooth_x - self.last_cursor_x) * velocity_scale
        scaled_y = self.last_cursor_y + (smooth_y - self.last_cursor_y) * velocity_scale
        
        # Clamp to valid range
        scaled_x = max(0.0, min(1.0, scaled_x))
        scaled_y = max(0.0, min(1.0, scaled_y))
        
        # Limit maximum velocity per frame
        final_x = self.last_cursor_x + np.clip(scaled_x - self.last_cursor_x, -self.max_velocity, self.max_velocity)
        final_y = self.last_cursor_y + np.clip(scaled_y - self.last_cursor_y, -self.max_velocity, self.max_velocity)
        
        self.last_cursor_x = final_x
        self.last_cursor_y = final_y
        
        return final_x, final_y
    
    def apply_dead_zone(self, raw_x, raw_y):
        """Apply dead zone near center to prevent shaking"""
        # Calculate distance from center
        dist_x = abs(raw_x - self.center_position)
        dist_y = abs(raw_y - self.center_y_position)
        
        if dist_x < self.dead_zone_radius:
            raw_x = self.center_position
        if dist_y < self.dead_zone_radius:
            raw_y = self.center_y_position
        
        return raw_x, raw_y
    
    def start_calibration(self):
        """Begin the multi-point calibration process"""
        self.calibration_mode = True
        self.calibration_step = 0
        self.calibration_samples = []
        self.sample_count = 0
        print("🎯 Starting calibration. Look at the center of the screen and hold steady...")
    
    def collect_calibration_sample(self, iris_pos_x, iris_pos_y):
        """Collect a sample for the current calibration point"""
        if not self.calibration_mode:
            return None
        
        self.calibration_samples.append((iris_pos_x, iris_pos_y))
        self.sample_count += 1
        
        if self.sample_count >= self.samples_per_point:
            # Average the samples for this calibration point
            avg_x = np.mean([s[0] for s in self.calibration_samples])
            avg_y = np.mean([s[1] for s in self.calibration_samples])
            
            # Store calibration point
            steps = ['center', 'top_left', 'top_right', 'bottom_left', 'bottom_right']
            self.calibration_points[steps[self.calibration_step]] = (avg_x, avg_y)
            
            print(f"✓ {steps[self.calibration_step].upper()} calibrated: ({avg_x:.3f}, {avg_y:.3f})")
            
            # Move to next calibration point
            self.calibration_step += 1
            self.calibration_samples = []
            self.sample_count = 0
            
            if self.calibration_step >= 5:
                # Calibration complete
                self.finish_calibration()
                return 'complete'
            else:
                # Next step
                next_steps = {
                    1: "👀 Now look at the TOP-LEFT corner",
                    2: "👀 Now look at the TOP-RIGHT corner",
                    3: "👀 Now look at the BOTTOM-LEFT corner",
                    4: "👀 Now look at the BOTTOM-RIGHT corner"
                }
                print(next_steps.get(self.calibration_step, "Calibration step"))
                return 'next'
        
        return 'collecting'
    
    def finish_calibration(self):
        """Complete calibration and calculate mapping"""
        self.calibration_mode = False
        
        center = self.calibration_points['center']
        tl = self.calibration_points['top_left']
        tr = self.calibration_points['top_right']
        bl = self.calibration_points['bottom_left']
        br = self.calibration_points['bottom_right']
        
        # Calculate center position
        self.center_position = center[0]
        self.center_y_position = center[1]
        
        # Calculate screen edges based on calibration
        self.calibrated = True
        print(f"""
✅ CALIBRATION COMPLETE!
━━━━━━━━━━━━━━━━━━━━━━━━━━
Center: ({center[0]:.3f}, {center[1]:.3f})
Top-Left: ({tl[0]:.3f}, {tl[1]:.3f})
Top-Right: ({tr[0]:.3f}, {tr[1]:.3f})
Bottom-Left: ({bl[0]:.3f}, {bl[1]:.3f})
Bottom-Right: ({br[0]:.3f}, {br[1]:.3f})
━━━━━━━━━━━━━━━━━━━━━━━━━━
Cursor is now calibrated for full screen coverage!
        """)
    
    def reset_filters(self):
        """Reset Kalman filters when calibration changes"""
        self.kalman_x = KalmanFilter1D(process_variance=0.0001, measurement_variance=0.001, initial_value=0.5)
        self.kalman_y = KalmanFilter1D(process_variance=0.0001, measurement_variance=0.001, initial_value=0.5)
        self.cursor_x_history.clear()
        self.cursor_y_history.clear()
        self.last_cursor_x = 0.5
        self.last_cursor_y = 0.5
    
    def detect_action(self, left_ear, right_ear, iris_pos_x, iris_pos_y, nose_x, nose_y):
        current_time = time.time()
        avg_ear = (left_ear + right_ear) / 2
        
        # Calculate normalized Y position (0 = top, 1 = bottom)
        normalized_y = iris_pos_y if self.calibrated else 0.5
        
        # Calculate raw cursor position (0.0 to 1.0 for full screen mapping)
        cursor_x = iris_pos_x
        cursor_y = iris_pos_y
        
        if self.calibrated and not self.calibration_mode:
            # Apply dead zone to prevent shaking
            cursor_x, cursor_y = self.apply_dead_zone(iris_pos_x, iris_pos_y)
            
            # Apply advanced smoothing with Kalman filter + moving average + velocity scaling
            cursor_x, cursor_y = self.smooth_cursor_position(cursor_x, cursor_y)
        
        action = {
            'direction': 'center',
            'accelerate': True,  # Default to accelerate
            'brake': False,
            'blink': False,
            'wink': None,
            'start_game': False,
            'iris_y': normalized_y,
            'head_x': nose_x if self.last_nose_x else 0.5,
            'head_y': nose_y if self.last_nose_y else 0.5,
            'cursor_x': cursor_x,  # Add cursor position for Gradio
            'cursor_y': cursor_y,  # Add cursor position for Gradio
            'left_wink': False,
            'right_wink': False,
            'action': None,
            'calibration_mode': self.calibration_mode
        }
        
        # Detect wink (one eye closed, other open) - STRICTER DETECTION
        ear_diff = abs(left_ear - right_ear)
        if ear_diff > 0.12:  # INCREASED from 0.08 - require bigger difference between eyes
            if left_ear < self.wink_threshold and right_ear > 0.25:  # STRICTER - other eye must be more open
                if current_time - self.last_blink_time > 0.8:  # INCREASED debounce
                    action['wink'] = 'left'
                    action['left_wink'] = True
                    action['action'] = 'wink'
                    self.last_blink_time = current_time
                    print("😉 LEFT WINK detected!")
            elif right_ear < self.wink_threshold and left_ear > 0.25:  # STRICTER - other eye must be more open
                if current_time - self.last_blink_time > 0.8:  # INCREASED debounce
                    action['wink'] = 'right'
                    action['right_wink'] = True
                    action['action'] = 'wink'
                    self.last_blink_time = current_time
                    print("😉 RIGHT WINK detected!")
        
        # Detect quick blink (both eyes closed briefly) - STRICTER DETECTION
        if avg_ear < self.blink_threshold and action['wink'] is None:
            if self.eyes_closed_start is None:
                self.eyes_closed_start = current_time
            
            # Check if eyes have been closed long enough to trigger action
            eyes_closed_duration = current_time - self.eyes_closed_start
            if eyes_closed_duration >= self.eyes_closed_duration and current_time - self.last_blink_time > 0.8:
                action['blink'] = True  # Only register if debounce allows
                action['brake'] = True
                action['accelerate'] = False
                self.last_blink_time = current_time
                print(f"🛑 BLINK detected - eyes closed for {eyes_closed_duration:.2f}s")
        else:
            # Eyes just opened - check if it was a blink or long press
            if self.eyes_closed_start is not None:
                eyes_closed_duration = current_time - self.eyes_closed_start
                
                # Quick blink detected (eyes were closed briefly)
                if eyes_closed_duration < 0.3 and current_time - self.last_blink_time > 0.5:
                    self.last_blink_time = current_time
                    action['blink'] = True
                    action['action'] = 'blink'
                    action['start_game'] = True
                    if not self.game_started:
                        self.game_started = True
                    print("😑 BLINK detected!")
                
                self.eyes_closed_start = None  # Reset
        
        # Detect direction (NATURAL: look left = turn left, look right = turn right)
        raw_direction = 'center'
        if self.calibrated:
            if iris_pos_x < self.look_left_threshold:
                raw_direction = 'left'  # Look left -> turn left
            elif iris_pos_x > self.look_right_threshold:
                raw_direction = 'right'   # Look right -> turn right
        
        # Apply smoothing to reduce jitter/latency
        self.direction_history.append(raw_direction)
        if len(self.direction_history) > self.history_size:
            self.direction_history.pop(0)
        
        # Use most common direction in history (minimal smoothing for fast response)
        if len(self.direction_history) >= 1:
            from collections import Counter
            direction_counts = Counter(self.direction_history)
            action['direction'] = direction_counts.most_common(1)[0][0]
        else:
            action['direction'] = raw_direction
        
        # Add cursor position data for Gradio interface
        action['cursor_x'] = cursor_x
        action['cursor_y'] = cursor_y
        
        return action
    
    async def broadcast(self, message):
        """Send message to all connected clients"""
        if self.clients:
            # Send to each client, ignore errors
            for client in list(self.clients):
                try:
                    await client.send(json.dumps(message))
                except Exception as e:
                    # Client disconnected, remove it
                    if client in self.clients:
                        self.clients.remove(client)
    
    async def handle_client(self, websocket):
        """Handle WebSocket client connection"""
        self.clients.add(websocket)
        print(f"🔌 Game connected! Total clients: {len(self.clients)}")
        try:
            await websocket.wait_closed()
        finally:
            if websocket in self.clients:
                self.clients.remove(websocket)
            print(f"🔌 Game disconnected! Total clients: {len(self.clients)}")
    
    def draw_visualization(self, frame, ear, iris_pos, action):
        """Draw overlay"""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        # Status box
        cv2.rectangle(overlay, (0, 0), (w, 120), (20, 20, 20), -1)
        frame = cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)
        
        cv2.putText(frame, "EYE TRACKING CONTROLLER", (20, 40), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 255), 2)
        
        status = "GAME ACTIVE" if self.game_started else "BLINK TO START"
        color = (0, 255, 0) if self.game_started else (0, 200, 255)
        cv2.putText(frame, status, (20, 85), cv2.FONT_HERSHEY_DUPLEX, 0.8, color, 2)
        
        # Connection status
        conn_text = f"Connected: {len(self.clients)}"
        conn_color = (0, 255, 0) if self.clients else (0, 0, 255)
        cv2.putText(frame, conn_text, (w - 200, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, conn_color, 2)
        
        # Bottom panel
        panel_y = h - 180
        cv2.rectangle(overlay, (0, panel_y), (w, h), (20, 20, 20), -1)
        frame = cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)
        
        # Direction indicator
        center_x = w // 2
        indicator_y = panel_y + 60
        
        if action['direction'] == 'left':
            cv2.arrowedLine(frame, (center_x + 50, indicator_y), 
                          (center_x - 80, indicator_y), (0, 255, 255), 12, tipLength=0.3)
            cv2.putText(frame, "LEFT", (center_x - 150, indicator_y + 50), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 255), 2)
        elif action['direction'] == 'right':
            cv2.arrowedLine(frame, (center_x - 50, indicator_y), 
                          (center_x + 80, indicator_y), (0, 255, 255), 12, tipLength=0.3)
            cv2.putText(frame, "RIGHT", (center_x + 20, indicator_y + 50), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 255), 2)
        else:
            cv2.circle(frame, (center_x, indicator_y), 20, (0, 255, 0), -1)
            cv2.putText(frame, "CENTER", (center_x - 60, indicator_y + 50), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
        
        # Acceleration
        if action['accelerate']:
            cv2.putText(frame, "ACCELERATING", (w - 250, panel_y + 130), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)
        
        # Brake indicator
        if action.get('brake', False):
            cv2.putText(frame, "BRAKING!", (w - 250, panel_y + 160), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 255), 2)
            cv2.rectangle(frame, (w - 260, panel_y + 100), (w - 20, panel_y + 120), (0, 0, 255), 3)
        
        # Eye position bar
        bar_y = panel_y + 25
        bar_w = w - 40
        cv2.rectangle(frame, (20, bar_y - 4), (20 + bar_w, bar_y + 4), (100, 100, 100), -1)
        
        marker_x = int(20 + iris_pos * bar_w)
        marker_color = (0, 255, 255) if action['direction'] != 'center' else (0, 255, 0)
        cv2.circle(frame, (marker_x, bar_y), 10, marker_color, -1)
        
        return frame
    
    async def process_video(self):
        """Process video and send controls"""
        # Try multiple camera indices with DirectShow backend
        cap = None
        for camera_idx in [0, 1, 2]:
            print(f"[*] Trying camera index {camera_idx}...")
            cap = cv2.VideoCapture(camera_idx, cv2.CAP_DSHOW)  # Use DirectShow for Windows
            if cap.isOpened():
                print(f"[OK] Camera {camera_idx} opened successfully!")
                break
            else:
                if cap:
                    cap.release()
                cap = None
        
        if cap is None or not cap.isOpened():
            print("\n" + "="*60)
            print("[ERROR] Cannot open webcam!")
            print("="*60)
            print("\n🔧 Troubleshooting:")
            print("  1. Close all apps using the camera (Teams, Zoom, Skype, etc.)")
            print("  2. Check if camera is connected properly")
            print("  3. Grant camera permissions in Windows Settings")
            print("  4. Try unplugging and reconnecting the camera")
            print("  5. Restart your computer")
            print("\n💡 Camera may be in use by another application!")
            print("="*60 + "\n")
            return
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        cv2.namedWindow('Eye Tracking', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Eye Tracking', 900, 600)
        cv2.moveWindow('Eye Tracking', 950, 100)
        
        print("\n[OK] Eye tracking started!")
        print("📡 Sending controls to game via WebSocket\n")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame = cv2.flip(frame, 1)
                frame_h, frame_w = frame.shape[:2]
                
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(rgb_frame)
                
                action = {'direction': 'center', 'accelerate': False, 'blink': False, 'start_game': False}
                
                if results.multi_face_landmarks:
                    landmarks = results.multi_face_landmarks[0].landmark
                    
                    left_ear = self.get_eye_aspect_ratio(self.LEFT_EYE, landmarks, frame_w, frame_h)
                    right_ear = self.get_eye_aspect_ratio(self.RIGHT_EYE, landmarks, frame_w, frame_h)
                    avg_ear = (left_ear + right_ear) / 2
                    
                    left_iris_x, left_iris_y = self.get_iris_position(self.LEFT_IRIS, self.LEFT_EYE, landmarks, frame_w, frame_h, is_left_eye=True)
                    right_iris_x, right_iris_y = self.get_iris_position(self.RIGHT_IRIS, self.RIGHT_EYE, landmarks, frame_w, frame_h, is_left_eye=False)
                    avg_iris_x = (left_iris_x + right_iris_x) / 2
                    avg_iris_y = (left_iris_y + right_iris_y) / 2
                    
                    # Get nose position for head tracking
                    nose_x = landmarks[1].x  # Nose tip
                    nose_y = landmarks[1].y
                    
                    if not self.calibrated:
                        self.calibrate(landmarks, frame_w, frame_h)
                    else:
                        # Update last nose position for head movement tracking
                        self.last_nose_x = nose_x
                        self.last_nose_y = nose_y
                    
                    action = self.detect_action(left_ear, right_ear, avg_iris_x, avg_iris_y, nose_x, nose_y)
                    frame = self.draw_visualization(frame, avg_ear, avg_iris_x, action)
                    
                    # Send to game
                    await self.broadcast(action)
                
                cv2.imshow('Eye Tracking', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                await asyncio.sleep(0.005)  # Reduced from 0.01 for faster updates
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    async def start(self, auto_open_browser=True):
        """Start WebSocket server and video processing"""
        try:
            # Start WebSocket server - bind to 0.0.0.0 to accept connections from any interface
            print("\n" + "="*70)
            print("[SERVER] Starting WebSocket server...")
            print("="*70)
            server = await websockets.serve(self.handle_client, "0.0.0.0", 8765)
            print("[✓] WebSocket server bound successfully on port 8765")
            print("[✓] Listening on ws://0.0.0.0:8765 (ws://localhost:8765)")
            print("[✓] Ready to accept client connections\n")
            
            # Only auto-open game menu if requested (not when launched from Gradio)
            if auto_open_browser:
                game_path = os.path.abspath("game_menu.html")
                print(f"[GAME] Opening game menu: {game_path}")
                webbrowser.open('file://' + game_path)
            
            print("\n" + "="*70)
            print("EYE TRACKING GAME CONTROL")
            print("="*70)
            print("* Look LEFT/RIGHT to steer")
            print("* BLINK to start game")
            print("* Eyes OPEN to accelerate")
            print("* Press 'Q' in video window to quit")
            print("="*70 + "\n")
            
            await asyncio.sleep(1)
            
            # Start video processing
            await self.process_video()
        except Exception as e:
            print(f"\n[ERROR] Error in start(): {e}")
            import traceback
            traceback.print_exc()
            raise

def main():
    import sys
    
    # Set UTF-8 encoding for console output to support emojis
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass
    
    # Quick camera check before starting async
    print("Checking camera availability...")
    test_cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not test_cap.isOpened():
        print("\n" + "="*60)
        print("ERROR: Cannot open webcam!")
        print("="*60)
        print("Camera is not accessible. Please:")
        print("  1. Close all apps using camera")
        print("  2. Check camera connection")
        print("  3. Grant camera permissions")
        print("="*60)
        test_cap.release()
        return
    test_cap.release()
    print("Camera is accessible\n")
    
    try:
        server = EyeTrackingServer()
        # Check if running from Gradio (no auto-open browser in that case)
        auto_open = '--no-browser' not in sys.argv
        asyncio.run(server.start(auto_open_browser=auto_open))
    except KeyboardInterrupt:
        print("\n[STOP] Eye tracker stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Eye tracker error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
