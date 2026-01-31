import gradio as gr
import webbrowser
import os
import subprocess
import threading
import time
import sys

# Get the absolute path to the project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Global variable to track eye tracker process
eye_tracker_process = None
eye_tracker_running = False

def start_eye_tracker():
    """Start the eye tracking WebSocket server"""
    global eye_tracker_process, eye_tracker_running
    
    if eye_tracker_running:
        return "✅ Eye tracker already running!"
    
    try:
        # Use the current Python executable (from the active virtual environment)
        python_exe = sys.executable
        eye_server = os.path.join(PROJECT_DIR, "eye_websocket_server.py")
        
        # Check if files exist
        if not os.path.exists(python_exe):
            return f"❌ Python executable not found at: {python_exe}"
        if not os.path.exists(eye_server):
            return f"❌ Eye server script not found at: {eye_server}"
        
        # Start process in background without showing console or auto-opening browser
        eye_tracker_process = subprocess.Popen(
            [python_exe, eye_server, '--no-browser'],
            cwd=PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait and check if it's running  
        time.sleep(3)
        
        if eye_tracker_process.poll() is None:
            eye_tracker_running = True
            return "✅ Eye tracker started successfully!\n📹 Webcam is now active.\n👁️ Look at the center of your screen to calibrate.\n🌐 WebSocket server running on ws://localhost:8765\n\n💡 Now you can launch games from the buttons below!"
        else:
            # Process exited - get full details
            eye_tracker_running = False
            try:
                stdout, stderr = eye_tracker_process.communicate(timeout=1)
                full_output = (stderr or "") + (stdout or "")
                
                # Filter out MediaPipe warnings (these are normal)
                error_lines = []
                for line in full_output.split('\n'):
                    if line.strip() and not any(x in line for x in ['INFO:', 'WARNING:', 'inference_feedback_manager', 'XNNPACK', 'absl::']):
                        error_lines.append(line)
                
                actual_errors = '\n'.join(error_lines)
                
                # Check for specific errors
                if "Cannot open webcam" in full_output:
                    return "❌ WEBCAM NOT ACCESSIBLE!\n\n🔧 Solutions:\n1. Close ALL apps using camera:\n   • Teams, Zoom, Skype, Discord\n   • OBS Studio, Streamlabs\n2. Check camera connection\n3. Windows Settings → Privacy → Camera\n4. Click '📹 Test Webcam' button"
                elif "OSError" in full_output or "10048" in full_output:
                    return "❌ Port 8765 already in use!\n\n💡 Another eye tracker is running.\n→ Close other Python windows\n→ Check Task Manager for python.exe"
                elif "Traceback" in actual_errors or "Error" in actual_errors:
                    return f"❌ Eye tracker crashed!\n\n{actual_errors[:800]}\n\n💡 Try:\n1. Test webcam (📹 button)\n2. Close camera apps\n3. Restart Gradio"
                elif len(actual_errors.strip()) < 50:
                    # No real errors, just warnings - might have closed window
                    return "⚠️ Eye tracker exited quickly.\n\nLikely causes:\n• Tracking window was closed\n• Camera briefly unavailable\n\n💡 Try starting again"
                else:
                    return f"❌ Unknown error:\n\n{actual_errors[:400]}"
            except Exception as ex:
                return f"❌ Error checking status: {str(ex)}\n\n💡 Try:\n1. Test webcam\n2. Close camera apps\n3. Run manually to see full error"
    except Exception as e:
        eye_tracker_running = False
        return f"❌ Error starting eye tracker: {str(e)}\n\nTroubleshooting:\n- Close any apps using your webcam\n- Check if .venv exists\n- Try running eye_websocket_server.py manually"

def stop_eye_tracker():
    """Stop the eye tracking WebSocket server"""
    global eye_tracker_process, eye_tracker_running
    
    if not eye_tracker_running:
        return "ℹ️ Eye tracker is not running."
    
    try:
        if eye_tracker_process:
            # Try graceful termination first
            eye_tracker_process.terminate()
            try:
                eye_tracker_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                eye_tracker_process.kill()
                eye_tracker_process.wait()
            
            eye_tracker_running = False
            return "⏹️ Eye tracker stopped successfully."
    except Exception as e:
        eye_tracker_running = False
        return f"⚠️ Eye tracker stopped (with error): {str(e)}"

def test_webcam():
    """Test if webcam is accessible"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                return "✅ Webcam is working! Camera detected and accessible."
            else:
                return "⚠️ Webcam detected but cannot read frames. Try closing other apps."
        else:
            return "❌ Cannot open webcam. Check if:\n- Webcam is connected\n- No other apps are using it\n- Camera permissions are enabled"
    except Exception as e:
        return f"❌ Webcam test failed: {str(e)}"

def get_tracker_status():
    """Get current status of eye tracker"""
    global eye_tracker_running
    if eye_tracker_running:
        return "🟢 Running"
    return "🔴 Stopped"

def launch_game(game_name):
    """Launch a specific game in the browser"""
    game_files = {
        "Game Menu": "game_menu.html",
        "Dash Racer": "index_eye_control.html",
        "Target Shooter": "shooting_game.html",
        "Western Shooter": "western_shooter.html",
        "Memory Match": "memory_game.html"
    }
    
    if game_name in game_files:
        file_path = os.path.join(PROJECT_DIR, game_files[game_name])
        file_url = f"file:///{file_path.replace(os.sep, '/')}"
        
        try:
            webbrowser.open(file_url)
            return f"🎮 Launching {game_name}...\n\n⚠️ Make sure eye tracker is running!\n👁️ Use your eyes/head to control the game."
        except Exception as e:
            return f"❌ Error launching game: {str(e)}"
    
    return "❌ Game not found!"

# Create Gradio interface
with gr.Blocks(title="Eye Control Games", theme=gr.themes.Soft()) as app:
    gr.Markdown("""
    # 👁️ Eye Control Games
    ### Control games with your eyes and head movements!
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("""
            ## 🎮 Eye Tracker Control
            Start the eye tracker before playing games.
            """)
            
            tracker_status = gr.Textbox(
                label="Eye Tracker Status",
                value="🔴 Stopped",
                interactive=False
            )
            
            with gr.Row():
                start_btn = gr.Button("▶️ Start Eye Tracker", variant="primary", size="lg")
                stop_btn = gr.Button("⏹️ Stop Eye Tracker", variant="stop", size="lg")
            
            test_cam_btn = gr.Button("📹 Test Webcam", size="sm")
            
            tracker_output = gr.Textbox(
                label="Tracker Messages",
                lines=5,
                interactive=False
            )
            
            gr.Markdown("""
            ### 👁️ Controls:
            - **Look Left/Right** - Steer/Move cursor
            - **Blink** 😑 - Start game/Shoot/Select
            - **Left Wink** 😉 - Special actions
            - **Keep eyes open** - Accelerate/Move
            """)
        
        with gr.Column(scale=2):
            gr.Markdown("## 🎯 Available Games")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("""
                    ### 🏎️ Dash Racer
                    Race through the track!
                    - Look left/right to steer
                    - Stay on track to survive
                    - Avoid boundaries for 5 seconds
                    """)
                    dash_btn = gr.Button("🏎️ Play Dash Racer", size="lg")
                    
                    gr.Markdown("""
                    ### 🎯 Target Shooter
                    Shoot flying birds with hats!
                    - Move head to aim cursor
                    - Blink to shoot
                    - 10-15 birds per wave
                    - Complete 10 waves to win
                    """)
                    shooter_btn = gr.Button("🎯 Play Target Shooter", size="lg")
                
                with gr.Column():
                    gr.Markdown("""
                    ### 🤠 Western Shooter
                    Desert stickman battle!
                    - Move head to aim
                    - Blink to shoot enemies
                    - Build combos & survive
                    """)
                    western_btn = gr.Button("🤠 Play Western Shooter", size="lg")
                    
                    gr.Markdown("""
                    ### 🧩 Memory Match
                    Find matching card pairs!
                    - Move head to move cursor
                    - Hover over cards
                    - Blink to flip cards
                    - Match all pairs to win
                    """)
                    memory_btn = gr.Button("🧩 Play Memory Match", size="lg")
            
            with gr.Row():
                menu_btn = gr.Button("🎮 Open Game Menu", variant="primary", size="lg", scale=2)
            
            game_output = gr.Textbox(
                label="Game Status",
                lines=4,
                interactive=False
            )

    
    # Button click handlers
    start_btn.click(
        fn=start_eye_tracker,
        outputs=tracker_output
    ).then(
        fn=get_tracker_status,
        outputs=tracker_status
    )
    
    stop_btn.click(
        fn=stop_eye_tracker,
        outputs=tracker_output
    ).then(
        fn=get_tracker_status,
        outputs=tracker_status
    )
    
    test_cam_btn.click(
        fn=test_webcam,
        outputs=tracker_output
    )
    
    menu_btn.click(
        fn=lambda: launch_game("Game Menu"),
        outputs=game_output
    )
    
    dash_btn.click(
        fn=lambda: launch_game("Dash Racer"),
        outputs=game_output
    )
    
    shooter_btn.click(
        fn=lambda: launch_game("Target Shooter"),
        outputs=game_output
    )
    
    western_btn.click(
        fn=lambda: launch_game("Western Shooter"),
        outputs=game_output
    )
    
    memory_btn.click(
        fn=lambda: launch_game("Memory Match"),
        outputs=game_output
    )

if __name__ == "__main__":
    print("🎮 Starting Eye Control Games Interface...")
    print("📂 Project directory:", PROJECT_DIR)
    print("🌐 Gradio interface will open in your browser...")
    
    try:
        app.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=True,
            inbrowser=True
        )
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down...")
        if eye_tracker_running:
            stop_eye_tracker()
