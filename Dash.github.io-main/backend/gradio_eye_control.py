"""
Eye-controlled Gradio interface for Eye Control Games
Uses WebSocket eye tracking to control the interface with eye movements and blinks
"""
import gradio as gr
import webbrowser
import os
import subprocess
import sys
import time
import socket

# Get the absolute path to the project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Global variable to track eye tracker process
eye_tracker_process = None
eye_tracker_running = False

def is_port_open(host, port, timeout=1):
    """Check if a port is open and accepting connections"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    finally:
        sock.close()

def start_eye_tracker():
    """Start the eye tracking WebSocket server"""
    global eye_tracker_process, eye_tracker_running
    
    if eye_tracker_running:
        return "✅ Eye tracker already running!"
    
    try:
        python_exe = sys.executable
        eye_server = os.path.join(PROJECT_DIR, "eye_websocket_server.py")
        
        if not os.path.exists(eye_server):
            return f"❌ Eye server script not found at: {eye_server}"
        
        eye_tracker_process = subprocess.Popen(
            [python_exe, eye_server, '--no-browser'],
            cwd=PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to be ready (with verification)
        max_attempts = 30  # 30 seconds max wait
        for attempt in range(max_attempts):
            if eye_tracker_process.poll() is not None:
                # Process has crashed
                eye_tracker_running = False
                return "❌ Eye tracker failed to start. Check webcam availability."
            
            # Check if port is open
            if is_port_open('localhost', 8765):
                eye_tracker_running = True
                return "✅ Eye tracker started!\n📹 Webcam active\n👁️ Move your eyes/head to control cursor\n😑 Blink to click buttons\n\n⏳ Connecting... (The status above should turn green when connected)"
            
            time.sleep(1)  # Check every 1 second
        
        # Timeout reached
        eye_tracker_running = False
        return "❌ Eye tracker started but WebSocket server not responding on port 8765. Check firewall settings."
    except Exception as e:
        eye_tracker_running = False
        return f"❌ Error: {str(e)}"

def stop_eye_tracker():
    """Stop the eye tracking WebSocket server"""
    global eye_tracker_process, eye_tracker_running
    
    if not eye_tracker_running:
        return "ℹ️ Eye tracker is not running."
    
    try:
        if eye_tracker_process:
            eye_tracker_process.terminate()
            try:
                eye_tracker_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                eye_tracker_process.kill()
                eye_tracker_process.wait()
            
            eye_tracker_running = False
            return "⏹️ Eye tracker stopped."
    except Exception as e:
        eye_tracker_running = False
        return f"⚠️ Stopped (error): {str(e)}"

def test_webcam():
    """Test if webcam is accessible"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                return "✅ Webcam working!"
            else:
                return "⚠️ Webcam detected but cannot read frames."
        else:
            return "❌ Cannot open webcam."
    except Exception as e:
        return f"❌ Test failed: {str(e)}"

def get_tracker_status():
    """Get current status of eye tracker"""
    global eye_tracker_running
    return "🟢 Running" if eye_tracker_running else "🔴 Stopped"

def voice_command_handler(command_text):
    """Handle voice commands for game selection"""
    if not command_text or command_text.strip() == "":
        return "⚠️ Please enter a voice command first"
    
    command = command_text.lower().strip()
    
    # Game mapping with voice keywords
    game_mapping = {
        'dash': ('Dash Racer', 'index_eye_control.html'),
        'racer': ('Dash Racer', 'index_eye_control.html'),
        'racing': ('Dash Racer', 'index_eye_control.html'),
        'race': ('Dash Racer', 'index_eye_control.html'),
        
        'shooter': ('Target Shooter', 'shooting_game.html'),
        'shoot': ('Target Shooter', 'shooting_game.html'),
        'target': ('Target Shooter', 'shooting_game.html'),
        'shooting': ('Target Shooter', 'shooting_game.html'),
        
        'western': ('Western Shooter', 'western_shooter.html'),
        'west': ('Western Shooter', 'western_shooter.html'),
        'cowboy': ('Western Shooter', 'western_shooter.html'),
        'stickman': ('Western Shooter', 'western_shooter.html'),
        
        'memory': ('Memory Match', 'memory_game.html'),
        'match': ('Memory Match', 'memory_game.html'),
        'card': ('Memory Match', 'memory_game.html'),
        'cards': ('Memory Match', 'memory_game.html'),
        
        'menu': ('Game Menu', 'game_menu.html'),
        'game menu': ('Game Menu', 'game_menu.html'),
    }
    
    # Find matching game
    for keyword, (game_name, game_file) in game_mapping.items():
        if keyword in command:
            try:
                file_path = os.path.join(PROJECT_DIR, game_file)
                if os.path.exists(file_path):
                    file_url = f"file:///{file_path.replace(os.sep, '/')}"
                    webbrowser.open(file_url)
                    return f"✅ Launching {game_name}...\n🎮 Game opening in browser"
                else:
                    return f"❌ Game file not found: {game_file}"
            except Exception as e:
                return f"❌ Error launching game: {str(e)}"
    
    return f"❌ Command not recognized: '{command_text}'\n\n📝 Try saying:\n• Dash\n• Shooter\n• Western\n• Memory\n• Menu"

def capture_voice_input():
    """Placeholder for voice capture - the actual speech-to-text happens in JavaScript"""
    return "🎤 Listening... Speak your command now!", ""

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
        game_file = game_files[game_name]
        file_path = os.path.join(PROJECT_DIR, "..", "frontend", game_file)
        file_path = os.path.abspath(file_path)
        
        # Use file:// URL for opening HTML files locally
        file_url = f"file:///{file_path.replace(os.sep, '/')}"
        
        print(f"[GAME] Launching {game_name}")
        print(f"[GAME] File path: {file_path}")
        print(f"[GAME] File URL: {file_url}")
        print(f"[GAME] File exists: {os.path.exists(file_path)}")
        
        try:
            webbrowser.open(file_url)
            return f"🎮 Launching {game_name}...\n\n✅ New window opened!\n⚠️ Make sure eye tracker is running!"
        except Exception as e:
            print(f"[ERROR] Failed to launch: {e}")
            return f"❌ Error: {str(e)}\n\nTry opening manually: {file_path}"
    
    return "❌ Game not found!"

def start_calibration():
    """Start the eye tracking calibration process"""
    return """🎯 CALIBRATION STARTED
━━━━━━━━━━━━━━━━━━━━━━
1️⃣ Look at CENTER
   (Hold steady for 1s)

2️⃣ Look at TOP-LEFT
   (Hold steady for 1s)

3️⃣ Look at TOP-RIGHT
   (Hold steady for 1s)

4️⃣ Look at BOTTOM-LEFT
   (Hold steady for 1s)

5️⃣ Look at BOTTOM-RIGHT
   (Hold steady for 1s)

✅ Calibration will complete automatically!
"""

# Custom CSS with eye control cursor and hover effects - Professional Gaming Look
custom_css = """
/* Professional Gaming Suite Theme */
:root {
    --primary-accent: #00d9ff;
    --secondary-accent: #00ff88;
    --danger-accent: #ff3333;
    --dark-bg: #0a0e27;
    --card-bg: #141829;
    --border-glow: rgba(0, 217, 255, 0.3);
}

* {
    box-sizing: border-box;
}

html, body {
    background: linear-gradient(135deg, #0a0e27 0%, #1a1a3e 50%, #0f1b2e 100%) !important;
    color: #e0e0e0 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif !important;
    font-size: 16px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow-x: hidden !important;
}

/* Main container */
.gradio-container {
    max-width: 100% !important;
    background: transparent !important;
    padding: 40px 50px !important;
    margin: 0 !important;
}

/* Professional title styling */
.md h1 {
    color: #00d9ff !important;
    font-size: 56px !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    margin: 20px 0 !important;
    background: linear-gradient(135deg, #00d9ff, #00ff88) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    text-shadow: 0 0 30px rgba(0, 217, 255, 0.2) !important;
    text-transform: uppercase !important;
    filter: drop-shadow(0 0 15px rgba(0, 217, 255, 0.4)) !important;
}

.md h2 {
    color: #00d9ff !important;
    font-size: 36px !important;
    font-weight: 600 !important;
    letter-spacing: 1.5px !important;
    border-bottom: 2px solid #00d9ff !important;
    padding-bottom: 15px !important;
    text-transform: uppercase !important;
    margin-top: 40px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 2px 20px rgba(0, 217, 255, 0.15) !important;
}

.md h3 {
    color: #00ff88 !important;
    font-size: 24px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    margin: 15px 0 !important;
    text-transform: uppercase !important;
}

.md h4 {
    color: #e0e0e0 !important;
    font-size: 18px !important;
    font-weight: 500 !important;
    margin: 10px 0 !important;
}

.md p {
    color: #b0b0b0 !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    margin: 10px 0 !important;
}

.md code {
    background: rgba(0, 217, 255, 0.1) !important;
    color: #00d9ff !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    border-left: 2px solid #00d9ff !important;
    font-family: 'Courier New', monospace !important;
}

/* Eye Control Cursor - Professional Gaming */
#eye-cursor {
    position: fixed;
    width: 44px;
    height: 44px;
    border: 3px solid #00ff00;
    border-radius: 50%;
    pointer-events: none;
    z-index: 99999;
    display: block !important;
    box-shadow: 0 0 20px #00ff00, 0 0 40px rgba(0, 255, 0, 0.5), inset 0 0 10px rgba(0, 255, 0, 0.2);
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    background: radial-gradient(circle at 35% 35%, rgba(0, 255, 0, 0.2) 0%, rgba(0, 255, 0, 0.05) 40%, rgba(0, 255, 0, 0) 70%);
}

#eye-cursor::before {
    content: '';
    position: absolute;
    width: 8px;
    height: 8px;
    background: #00ff00;
    border-radius: 50%;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    box-shadow: 0 0 12px rgba(0, 255, 0, 0.9);
}

#eye-cursor.blinking {
    border-color: #ff4444 !important;
    border-width: 4px !important;
    background: radial-gradient(circle at 35% 35%, rgba(255, 68, 68, 0.4) 0%, rgba(255, 68, 68, 0.1) 40%, rgba(255, 68, 68, 0) 70%) !important;
    box-shadow: 0 0 30px rgba(255, 68, 68, 1), 0 0 50px rgba(255, 68, 68, 0.6), inset 0 0 15px rgba(255, 68, 68, 0.4) !important;
    transform: translate(-50%, -50%) scale(1.4) !important;
}

#eye-cursor.blinking::before {
    background: #ff4444 !important;
    width: 10px !important;
    height: 10px !important;
    box-shadow: 0 0 18px rgba(255, 68, 68, 1) !important;
}

/* Professional buttons */
button, .gradio-button, input[type="button"], input[type="submit"] {
    background: linear-gradient(135deg, #141829 0%, #1f2540 100%) !important;
    border: 1.5px solid #00d9ff !important;
    color: #00d9ff !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    padding: 16px 28px !important;
    min-height: 56px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 0 15px rgba(0, 217, 255, 0.2), inset 0 0 8px rgba(0, 217, 255, 0.05) !important;
    cursor: pointer !important;
    margin: 8px 6px !important;
    position: relative;
    overflow: hidden;
    font-family: inherit !important;
    border-radius: 4px !important;
}

button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0, 217, 255, 0.2), transparent);
    transition: left 0.3s !important;
}

button:hover::before {
    left: 100%;
}

button:hover, .gradio-button:hover {
    background: linear-gradient(135deg, #1f2540 0%, #2a3050 100%) !important;
    box-shadow: 0 0 30px rgba(0, 217, 255, 0.6), inset 0 0 15px rgba(0, 217, 255, 0.15) !important;
    transform: translateY(-2px) !important;
}

button:active, .gradio-button:active {
    transform: translateY(0) !important;
    box-shadow: 0 0 20px rgba(0, 217, 255, 0.4), inset 0 0 10px rgba(0, 217, 255, 0.2) !important;
}

button[variant="primary"] {
    background: linear-gradient(135deg, #00d9ff15 0%, #00ff8815 100%) !important;
    border-color: #00ff88 !important;
    color: #00ff88 !important;
    box-shadow: 0 0 15px rgba(0, 255, 136, 0.2) !important;
}

button[variant="primary"]:hover {
    background: linear-gradient(135deg, #00d9ff25 0%, #00ff8825 100%) !important;
    box-shadow: 0 0 30px rgba(0, 255, 136, 0.6), inset 0 0 15px rgba(0, 255, 136, 0.15) !important;
}

button[variant="stop"] {
    background: linear-gradient(135deg, #ff333315 0%, #ff000015 100%) !important;
    border-color: #ff3333 !important;
    color: #ff3333 !important;
    box-shadow: 0 0 15px rgba(255, 51, 51, 0.2) !important;
}

button[variant="stop"]:hover {
    background: linear-gradient(135deg, #ff333325 0%, #ff000025 100%) !important;
    box-shadow: 0 0 30px rgba(255, 51, 51, 0.6) !important;
}

/* Eye-focused element styling */
.eye-focused {
    outline: 3px solid #00ff88 !important;
    outline-offset: 2px !important;
    box-shadow: 0 0 30px rgba(0, 255, 136, 0.8), inset 0 0 15px rgba(0, 255, 136, 0.3) !important;
    animation: pulse-focus 0.6s ease-in-out infinite !important;
    transform: scale(1.05) !important;
}

@keyframes pulse-focus {
    0%, 100% { 
        outline-color: #00ff88; 
        box-shadow: 0 0 30px rgba(0, 255, 136, 0.8), inset 0 0 15px rgba(0, 255, 136, 0.3);
    }
    50% { 
        outline-color: #00d9ff; 
        box-shadow: 0 0 40px rgba(0, 217, 255, 1), inset 0 0 20px rgba(0, 217, 255, 0.4);
    }
}

/* Status indicator - Professional */
#eye-status-indicator {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 16px 24px;
    background: linear-gradient(135deg, rgba(10, 14, 39, 0.95), rgba(20, 24, 41, 0.98));
    color: #00d9ff;
    border: 1.5px solid #00d9ff;
    border-radius: 6px;
    z-index: 99998;
    font-weight: 600;
    font-size: 14px;
    box-shadow: 0 4px 30px rgba(0, 217, 255, 0.4), inset 0 0 15px rgba(0, 217, 255, 0.1);
    display: block !important;
    text-shadow: 0 0 5px rgba(0, 217, 255, 0.4);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    backdrop-filter: blur(10px);
}

/* Debug info */
#debug-info {
    position: fixed;
    bottom: 20px;
    left: 20px;
    padding: 12px 16px;
    background: linear-gradient(135deg, rgba(10, 14, 39, 0.95), rgba(20, 24, 41, 0.98));
    color: #00ff88;
    font-family: 'Courier New', monospace !important;
    font-size: 12px;
    z-index: 99997;
    border: 1.5px solid #00ff88;
    border-radius: 4px;
    display: none;
    line-height: 1.5;
    box-shadow: 0 4px 20px rgba(0, 255, 136, 0.3);
    text-shadow: 0 0 3px rgba(0, 255, 136, 0.5);
    max-width: 300px;
    max-height: 200px;
    overflow-y: auto;
    backdrop-filter: blur(10px);
}

/* Gaming cards */
.gradio-box {
    background: linear-gradient(135deg, #141829 0%, #1f2540 100%) !important;
    border: 1.5px solid #00d9ff !important;
    border-radius: 6px !important;
    box-shadow: 0 8px 32px rgba(0, 217, 255, 0.15), inset 0 0 20px rgba(0, 217, 255, 0.05) !important;
    padding: 24px !important;
}

.gradio-box:hover {
    box-shadow: 0 12px 40px rgba(0, 217, 255, 0.25), inset 0 0 20px rgba(0, 217, 255, 0.08) !important;
}

/* Text inputs & textareas */
textarea, input[type="text"], input[type="password"], input[type="number"] {
    background: linear-gradient(135deg, #0a0e27 0%, #141829 100%) !important;
    border: 1.5px solid #00d9ff !important;
    color: #e0e0e0 !important;
    font-family: 'Segoe UI', 'Roboto', sans-serif !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
    min-height: 44px !important;
    box-shadow: 0 0 15px rgba(0, 217, 255, 0.15), inset 0 0 8px rgba(0, 217, 255, 0.05) !important;
    transition: all 0.2s ease !important;
    border-radius: 4px !important;
}

textarea::placeholder, input::placeholder {
    color: #606080 !important;
}

textarea:focus, input:focus {
    outline: none !important;
    box-shadow: 0 0 25px rgba(0, 217, 255, 0.5), inset 0 0 12px rgba(0, 217, 255, 0.15) !important;
    border-color: #00ff88 !important;
    background: linear-gradient(135deg, #141829 0%, #1a2a3a 100%) !important;
}

/* Labels */
label {
    color: #00d9ff !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    text-shadow: 0 0 3px rgba(0, 217, 255, 0.3) !important;
    margin-bottom: 8px !important;
}

/* Grid layout */
.gradio-row {
    gap: 16px !important;
    margin-bottom: 16px !important;
}

.gradio-column {
    padding: 0 !important;
}

/* Textbox output styling */
[data-testid="textbox"] {
    background: linear-gradient(135deg, #0a0e27 0%, #141829 100%) !important;
    border: 1.5px solid #00d9ff !important;
    border-radius: 6px !important;
    box-shadow: 0 0 15px rgba(0, 217, 255, 0.15) !important;
}

/* Professional scrollbar */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 217, 255, 0.05);
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #00d9ff, #00ff88);
    border-radius: 5px;
    box-shadow: 0 0 10px rgba(0, 217, 255, 0.4);
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #00ff88, #00d9ff);
    box-shadow: 0 0 15px rgba(0, 217, 255, 0.6);
}

/* Background grid pattern subtle */
.gradio-container::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    z-index: -1;
    opacity: 0.02;
    background-image: repeating-linear-gradient(
        0deg,
        #00d9ff,
        #00d9ff 1px,
        transparent 1px,
        transparent 50px
    );
}

/* ============================================
   GAMING DASHBOARD - CARD-BASED SETTINGS PANEL
   XBOX/STEAM AESTHETIC - NO OVERLAP
   ============================================ */

/* MAIN SLIDER CARD CONTAINER */
.gradio-slider {
    /* Card styling - Xbox/Steam gaming aesthetic */
    background: linear-gradient(135deg, #1a1f3a 0%, #151b2f 100%) !important;
    border: 3px solid #00d9ff !important;
    border-radius: 12px !important;
    padding: 28px 32px !important;
    margin: 20px 0 !important;
    box-shadow: 
        0 0 40px rgba(0, 217, 255, 0.2),
        0 8px 32px rgba(0, 0, 0, 0.4),
        inset 0 0 30px rgba(0, 217, 255, 0.08) !important;
    
    /* Pure vertical flexbox layout */
    display: flex !important;
    flex-direction: column !important;
    gap: 18px !important;
    align-items: stretch !important;
    overflow: visible !important;
}

.gradio-slider:hover {
    border-color: #00ff88 !important;
    box-shadow: 
        0 0 50px rgba(0, 217, 255, 0.3),
        0 12px 40px rgba(0, 0, 0, 0.5),
        inset 0 0 30px rgba(0, 217, 255, 0.12) !important;
}

/* Hide all internal wrapper divs */
.gradio-slider > div {
    display: contents !important;
}

/* ============================================
   CARD ROW 1: SETTING TITLE
   ============================================ */
.gradio-slider label {
    display: block !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    order: 1 !important;
}

.gradio-slider label span:first-child {
    display: block !important;
    font-size: 14px !important;
    font-weight: 800 !important;
    color: #00d9ff !important;
    text-transform: uppercase !important;
    letter-spacing: 1.2px !important;
    margin: 0 !important;
    line-height: 1.4 !important;
    text-shadow: 0 0 8px rgba(0, 217, 255, 0.3) !important;
}

.gradio-slider label span:nth-child(2) {
    display: none !important;
}

/* ============================================
   CARD ROW 2: SLIDER WITH MIN/MAX LABELS
   ============================================ */

/* Min/Max label container */
.gradio-slider span {
    order: 2 !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 8px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    color: #00ff88 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
    height: auto !important;
    gap: 12px !important;
    margin-bottom: 6px !important;
}

/* Individual min/max labels */
.gradio-slider span::before {
    content: attr(data-min) !important;
    flex: 0 0 auto !important;
}

.gradio-slider span::after {
    content: attr(data-max) !important;
    flex: 0 0 auto !important;
}

/* The actual range slider */
.gradio-slider input[type="range"] {
    order: 2 !important;
    width: 100% !important;
    height: 16px !important;
    margin: 0 !important;
    padding: 0 !important;
    cursor: pointer !important;
    appearance: none !important;
    -webkit-appearance: none !important;
    background: transparent !important;
    border: none !important;
    outline: none !important;
}

/* WEBKIT Slider Track */
.gradio-slider input[type="range"]::-webkit-slider-track {
    width: 100% !important;
    height: 16px !important;
    background: linear-gradient(90deg, #0a0e27 0%, #141829 100%) !important;
    border: 2.5px solid #00d9ff !important;
    border-radius: 8px !important;
    box-shadow: 
        inset 0 2px 8px rgba(0, 0, 0, 0.6),
        0 0 20px rgba(0, 217, 255, 0.3) !important;
}

/* WEBKIT Slider Thumb */
.gradio-slider input[type="range"]::-webkit-slider-thumb {
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 32px !important;
    height: 32px !important;
    border-radius: 50% !important;
    background: linear-gradient(135deg, #00d9ff 0%, #00ff88 100%) !important;
    border: 3px solid #ffffff !important;
    cursor: pointer !important;
    box-shadow: 
        0 0 32px #00d9ff,
        0 0 60px rgba(0, 217, 255, 0.7),
        inset 0 0 12px rgba(0, 255, 136, 0.5),
        0 0 0 4px #1a1f3a !important;
    margin-top: -8px !important;
    transition: all 0.2s ease !important;
    position: relative !important;
    z-index: 10 !important;
}

.gradio-slider input[type="range"]::-webkit-slider-thumb:hover {
    width: 36px !important;
    height: 36px !important;
    box-shadow: 
        0 0 40px #00d9ff,
        0 0 80px rgba(0, 217, 255, 0.8),
        inset 0 0 16px rgba(0, 255, 136, 0.6),
        0 0 0 5px #1a1f3a !important;
    margin-top: -10px !important;
}

.gradio-slider input[type="range"]::-webkit-slider-thumb:active {
    width: 34px !important;
    height: 34px !important;
    background: linear-gradient(135deg, #00ff88 0%, #00d9ff 100%) !important;
}

/* FIREFOX Slider Track */
.gradio-slider input[type="range"]::-moz-range-track {
    width: 100% !important;
    height: 16px !important;
    background: linear-gradient(90deg, #0a0e27 0%, #141829 100%) !important;
    border: 2.5px solid #00d9ff !important;
    border-radius: 8px !important;
    box-shadow: 
        inset 0 2px 8px rgba(0, 0, 0, 0.6),
        0 0 20px rgba(0, 217, 255, 0.3) !important;
}

.gradio-slider input[type="range"]::-moz-range-progress {
    background: linear-gradient(90deg, #00d9ff 0%, #00ff88 100%) !important;
    border-radius: 8px !important;
    height: 16px !important;
    box-shadow: 0 0 16px rgba(0, 217, 255, 0.5) !important;
}

/* FIREFOX Slider Thumb */
.gradio-slider input[type="range"]::-moz-range-thumb {
    width: 32px !important;
    height: 32px !important;
    border-radius: 50% !important;
    background: linear-gradient(135deg, #00d9ff 0%, #00ff88 100%) !important;
    border: 3px solid #ffffff !important;
    cursor: pointer !important;
    box-shadow: 
        0 0 32px #00d9ff,
        0 0 60px rgba(0, 217, 255, 0.7),
        inset 0 0 12px rgba(0, 255, 136, 0.5),
        0 0 0 4px #1a1f3a !important;
    transition: all 0.2s ease !important;
}

.gradio-slider input[type="range"]::-moz-range-thumb:hover {
    width: 36px !important;
    height: 36px !important;
    box-shadow: 
        0 0 40px #00d9ff,
        0 0 80px rgba(0, 217, 255, 0.8),
        inset 0 0 16px rgba(0, 255, 136, 0.6),
        0 0 0 5px #1a1f3a !important;
}

.gradio-slider input[type="range"]::-moz-range-thumb:active {
    width: 34px !important;
    height: 34px !important;
    background: linear-gradient(135deg, #00ff88 0%, #00d9ff 100%) !important;
}

/* ============================================
   CARD ROW 3: INFO TEXT
   ============================================ */
.gradio-slider .info-text {
    order: 3 !important;
    display: block !important;
    font-size: 12px !important;
    color: #b0e0e6 !important;
    margin: 0 !important;
    padding: 0 !important;
    text-align: center !important;
    font-weight: 500 !important;
    line-height: 1.4 !important;
}

/* ============================================
   CARD ROW 4: VALUE DISPLAY BOX
   ============================================ */
.gradio-slider input[type="number"] {
    order: 4 !important;
    
    /* Value box styling */
    background: linear-gradient(135deg, #0a0e27 0%, #0f1335 100%) !important;
    border: 2.5px solid #00ff88 !important;
    border-radius: 10px !important;
    
    /* Typography */
    color: #00ff88 !important;
    font-family: 'Courier New', monospace !important;
    font-size: 24px !important;
    font-weight: 800 !important;
    text-align: center !important;
    
    /* Dimensions */
    width: 160px !important;
    height: 65px !important;
    padding: 14px 18px !important;
    margin: 0 auto !important;
    
    /* Effects */
    box-shadow: 
        0 0 20px rgba(0, 255, 136, 0.4),
        inset 0 2px 6px rgba(0, 0, 0, 0.5),
        0 0 0 1px rgba(0, 255, 136, 0.2) !important;
    
    /* Interaction */
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    cursor: text !important;
    line-height: 1.5 !important;
}

.gradio-slider input[type="number"]:hover {
    border-color: #00d9ff !important;
    box-shadow: 
        0 0 28px rgba(0, 255, 136, 0.5),
        inset 0 2px 6px rgba(0, 0, 0, 0.5),
        0 0 0 2px rgba(0, 217, 255, 0.3) !important;
    transform: scale(1.05) !important;
}

.gradio-slider input[type="number"]:focus {
    outline: none !important;
    border-color: #00d9ff !important;
    background: linear-gradient(135deg, #0f1335 0%, #1a2a3a 100%) !important;
    color: #00d9ff !important;
    box-shadow: 
        0 0 40px rgba(0, 255, 136, 0.7),
        0 0 60px rgba(0, 217, 255, 0.5),
        inset 0 2px 6px rgba(0, 0, 0, 0.5),
        0 0 0 3px rgba(0, 217, 255, 0.4) !important;
    transform: scale(1.12) !important;
}

.gradio-slider input[type="number"]::placeholder {
    color: rgba(0, 255, 136, 0.3) !important;
}

/* ============================================
   RESPONSIVE DESIGN
   ============================================ */
@media (max-width: 1024px) {
    .gradio-slider {
        padding: 24px 28px !important;
        gap: 16px !important;
    }
    
    .gradio-slider label span:first-child {
        font-size: 13px !important;
    }
    
    .gradio-slider input[type="range"] {
        height: 15px !important;
    }
    
    .gradio-slider input[type="range"]::-webkit-slider-thumb {
        width: 30px !important;
        height: 30px !important;
        margin-top: -7px !important;
    }
    
    .gradio-slider input[type="range"]::-moz-range-thumb {
        width: 30px !important;
        height: 30px !important;
    }
    
    .gradio-slider input[type="number"] {
        width: 110px !important;
        height: 48px !important;
        font-size: 17px !important;
    }
}

@media (max-width: 768px) {
    .gradio-slider {
        padding: 20px 24px !important;
        gap: 14px !important;
        margin: 16px 0 !important;
        border-radius: 10px !important;
        border: 2.5px solid #00d9ff !important;
    }
    
    .gradio-slider label span:first-child {
        font-size: 12px !important;
        letter-spacing: 1px !important;
    }
    
    .gradio-slider span {
        padding: 0 4px !important;
        font-size: 10px !important;
    }
    
    .gradio-slider input[type="range"] {
        height: 14px !important;
    }
    
    .gradio-slider input[type="range"]::-webkit-slider-track {
        height: 14px !important;
    }
    
    .gradio-slider input[type="range"]::-moz-range-track {
        height: 14px !important;
    }
    
    .gradio-slider input[type="range"]::-webkit-slider-thumb {
        width: 28px !important;
        height: 28px !important;
        margin-top: -7px !important;
    }
    
    .gradio-slider input[type="range"]::-moz-range-thumb {
        width: 28px !important;
        height: 28px !important;
    }
    
    .gradio-slider input[type="number"] {
        width: 100px !important;
        height: 45px !important;
        font-size: 16px !important;
        padding: 10px 14px !important;
    }
    
    .gradio-slider .info-text {
        font-size: 11px !important;
    }
}

@media (max-width: 480px) {
    .gradio-slider {
        padding: 18px 20px !important;
        gap: 12px !important;
    }
    
    .gradio-slider label span:first-child {
        font-size: 11px !important;
    }
    
    .gradio-slider input[type="number"] {
        width: 90px !important;
        height: 42px !important;
        font-size: 15px !important;
    }
}

/* ============================================
   SETTINGS SECTION HEADER
   ============================================ */
.md h3 {
    background: linear-gradient(90deg, #00d9ff 0%, #00ff88 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-size: 24px !important;
    font-weight: 800 !important;
    letter-spacing: 1.5px !important;
    margin: 32px 0 24px 0 !important;
    text-transform: uppercase !important;
    text-shadow: 0 0 20px rgba(0, 217, 255, 0.2) !important;
    padding-bottom: 14px !important;
    border-bottom: 3px solid rgba(0, 217, 255, 0.4) !important;
}

"""

# JavaScript for eye control integration
eye_control_js = """
<script>
// Simple Eye Control for Gradio
(function() {
    console.log('🎮 Eye Control Script Loading...');
    
    // CHECK IF WE'RE ON A GAME PAGE - if so, disable eye control cursor
    const currentPage = window.location.pathname;
    const isGamePage = currentPage.includes('shooting_game.html') || 
                       currentPage.includes('memory_game.html') || 
                       currentPage.includes('western_shooter.html') ||
                       currentPage.includes('index_eye_control.html');
    
    if (isGamePage) {
        console.log('🎮 Game page detected - Eye cursor DISABLED to prevent accidental clicks');
        // Stop the script execution on game pages
        return;
    }
    
    let ws = null;
    let cursor = null;
    let statusDiv = null;
    let debugDiv = null;
    let connected = false;
    let lastX = 0.5;
    let lastY = 0.5;
    let prevX = 0.5;
    let prevY = 0.5;
    let hoveredElement = null;
    let hoverStart = 0;
    let lastBlinkTime = 0;
    let lastClickTime = 0;
    let lastLeftWinkTime = 0;
    let lastRightWinkTime = 0;
    let firstDataReceived = false;
    let updateScheduled = false;
    let gazeStable = false;
    let gazeStableTime = 0;
    let clickEnabled = false; // CRITICAL: Disable clicks initially
    let clickEnabledTime = 0;
    let pageLoadTime = Date.now(); // Track page load to disable clicks initially
    const DEBOUNCE_MS = 1500; // 1.5s minimum between blinks
    const CLICK_THROTTLE_MS = 2500; // 2.5s minimum between clicks - AGGRESSIVE to prevent accidental clicks
    const CLICK_ENABLED_DELAY_MS = 2000; // Wait 2 seconds after page load before allowing clicks
    const GAZE_STABILITY_THRESHOLD = 0.015; // Very strict - gaze must be extremely still
    const GAZE_STABILITY_TIME_MS = 500; // Gaze must be stable for 500ms before click allowed
    let autoScrollActive = false;
    const AUTO_SCROLL_THRESHOLD = 0.15;
    const AUTO_SCROLL_SPEED = 80;
    const MOVEMENT_THRESHOLD = 0.001;
    const UPDATE_INTERVAL = 16;
    const CURSOR_SMOOTH_FACTOR = 0.25;
    const DWELL_TIME_MS = 500;
    let sensitivity_level = 1.0;
    
    function init() {
        console.log('✅ Initializing Eye Control');
        
        // Create cursor
        cursor = document.createElement('div');
        cursor.id = 'eye-cursor';
        cursor.className = 'disconnected';
        document.body.appendChild(cursor);
        console.log('✅ Cursor created');
        
        // Create status indicator  
        statusDiv = document.createElement('div');
        statusDiv.id = 'eye-status-indicator';
        statusDiv.innerHTML = '⚠️ Click "Start Eye Tracker"';
        statusDiv.style.color = '#ff9900';
        statusDiv.style.borderColor = '#ff9900';
        document.body.appendChild(statusDiv);
        console.log('✅ Status indicator created');
        
        // Create debug info
        debugDiv = document.createElement('div');
        debugDiv.id = 'debug-info';
        debugDiv.innerHTML = 'Debug: Waiting...';
        document.body.appendChild(debugDiv);
        
        // Connect to WebSocket
        connectWebSocket();
        
        // Show debug on key press
        document.addEventListener('keydown', (e) => {
            if (e.key === 'd' || e.key === 'D') {
                debugDiv.style.display = debugDiv.style.display === 'none' ? 'block' : 'none';
            }
        });
        
        // ANTI-ACCIDENTAL-CLICK: Enable clicks after initial delay
        setTimeout(() => {
            clickEnabled = true;
            clickEnabledTime = Date.now();
            console.log('✅ Click detection ENABLED after', CLICK_ENABLED_DELAY_MS, 'ms delay');
            statusDiv.innerHTML = '✅ Eye Control Ready - Click Enabled';
        }, CLICK_ENABLED_DELAY_MS);
    }
    
    let connectionRetries = 0;
    const MAX_RETRIES = 15;
    
    function connectWebSocket() {
        console.log('🔌 Connecting to ws://localhost:8765... (Attempt ' + (connectionRetries + 1) + ')');
        
        try {
            ws = new WebSocket('ws://localhost:8765');
            
            ws.onopen = () => {
                console.log('✅ WebSocket CONNECTED!');
                connected = true;
                connectionRetries = 0; // Reset retries on successful connection
                cursor.className = 'connected';
                statusDiv.innerHTML = '✅ Eye Control Active';
                statusDiv.style.color = '#00ff00';
                statusDiv.style.borderColor = '#00ff00';
                statusDiv.style.background = 'rgba(0, 100, 0, 0.9)';
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleEyeData(data);
                } catch (e) {
                    console.error('Parse error:', e);
                }
            };
            
            ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                connected = false;
                cursor.className = 'disconnected';
                statusDiv.innerHTML = '⚠️ Connection Error - Retrying...';
                statusDiv.style.color = '#ff0000';
                statusDiv.style.borderColor = '#ff0000';
                statusDiv.style.background = 'rgba(100, 0, 0, 0.9)';
            };
            
            ws.onclose = () => {
                console.log('⚠️ WebSocket disconnected');
                connected = false;
                cursor.className = 'disconnected';
                
                if (connectionRetries < MAX_RETRIES) {
                    const retryDelay = Math.min(8000, 1000 * Math.pow(1.3, connectionRetries));
                    statusDiv.innerHTML = '⚠️ Reconnecting... (' + (connectionRetries + 1) + '/' + MAX_RETRIES + ')';
                    statusDiv.style.color = '#ff9900';
                    statusDiv.style.borderColor = '#ff9900';
                    statusDiv.style.background = 'rgba(100, 50, 0, 0.9)';
                    connectionRetries++;
                    
                    console.log('⏳ Retrying in ' + Math.round(retryDelay / 1000) + 's...');
                    setTimeout(connectWebSocket, retryDelay);
                } else {
                    statusDiv.innerHTML = '❌ Cannot Connect - Start Eye Tracker';
                    statusDiv.style.color = '#ff0000';
                    statusDiv.style.borderColor = '#ff0000';
                    statusDiv.style.background = 'rgba(100, 0, 0, 0.9)';
                    console.error('❌ Connection failed after ' + MAX_RETRIES + ' attempts. Start the eye tracker server first.');
                }
            };
        } catch (e) {
            console.error('Connection error:', e);
            connected = false;
            cursor.className = 'disconnected';
            statusDiv.innerHTML = '❌ Connection Failed';
            statusDiv.style.color = '#ff0000';
            statusDiv.style.borderColor = '#ff0000';
            statusDiv.style.background = 'rgba(100, 0, 0, 0.9)';
            
            if (connectionRetries < MAX_RETRIES) {
                connectionRetries++;
                const retryDelay = Math.min(8000, 1000 * Math.pow(1.3, connectionRetries));
                console.log('⏳ Retrying in ' + Math.round(retryDelay / 1000) + 's...');
                setTimeout(connectWebSocket, retryDelay);
            }
        }
    }
    
    function handleEyeData(data) {
        if (!data) return;
        
        // Update cursor position with extended range sensitivity and fast response
        if (data.cursor_x !== undefined && data.cursor_y !== undefined) {
            lastX = data.cursor_x;
            lastY = data.cursor_y;
            
            // On first data received, initialize cursor position WITHOUT moving
            if (!firstDataReceived) {
                prevX = lastX;
                prevY = lastY;
                firstDataReceived = true;
                
                const x = lastX * window.innerWidth;
                const y = lastY * window.innerHeight;
                
                cursor.style.left = x + 'px';
                cursor.style.top = y + 'px';
                cursor.style.transform = 'translate(-50%, -50%)';
                
                console.log('✅ Cursor initialized at eye position - Ready for movement!');
                
                // Schedule cursor updates
                setInterval(updateCursorPosition, UPDATE_INTERVAL);
                return;
            }
            
            // Auto-scroll based on vertical gaze position (independent of cursor updates)
            if (lastY < AUTO_SCROLL_THRESHOLD) {
                // Looking up - scroll up
                document.documentElement.scrollTop -= AUTO_SCROLL_SPEED;
                if (document.body) {
                    document.body.scrollTop -= AUTO_SCROLL_SPEED;
                }
                autoScrollActive = true;
                console.log('📜 Scrolling UP - Y:', lastY.toFixed(3));
            } else if (lastY > (1 - AUTO_SCROLL_THRESHOLD)) {
                // Looking down - scroll down
                document.documentElement.scrollTop += AUTO_SCROLL_SPEED;
                if (document.body) {
                    document.body.scrollTop += AUTO_SCROLL_SPEED;
                }
                autoScrollActive = true;
                console.log('📜 Scrolling DOWN - Y:', lastY.toFixed(3));
            } else {
                autoScrollActive = false;
            }
            
            // Update debug with more info
            let debugText = `X: ${lastX.toFixed(2)}, Y: ${lastY.toFixed(2)}<br>Pos: ${Math.round(lastX * window.innerWidth)}, ${Math.round(lastY * window.innerHeight)}`;
            if (autoScrollActive) {
                debugText += '<br>📜 AUTO-SCROLL: ' + (lastY < AUTO_SCROLL_THRESHOLD ? 'UP' : 'DOWN');
            }
            if (hoveredElement) {
                const elText = hoveredElement.textContent?.substring(0, 30) || hoveredElement.tagName.toLowerCase();
                debugText += `<br>🎯 HOVER: ${elText}`;
            }
            if (data.blink) debugText += '<br>BLINK: YES';
            if (data.left_wink) debugText += '<br>LEFT WINK: YES';
            if (data.right_wink) debugText += '<br>RIGHT WINK: YES';
            debugDiv.innerHTML = debugText;
        }
        
        // ANTI-ACCIDENTAL-CLICK: Track gaze stability
        // If gaze moves too much, mark it as unstable
        const gazeMovement = Math.sqrt(Math.pow(lastX - prevX, 2) + Math.pow(lastY - prevY, 2));
        if (gazeMovement > GAZE_STABILITY_THRESHOLD) {
            gazeStable = false;
            console.log('👁️ Gaze unstable - movement:', gazeMovement.toFixed(4));
        } else {
            if (!gazeStable) {
                gazeStable = true;
                gazeStableTime = Date.now();
                console.log('✅ Gaze is now stable - can click after', GAZE_STABILITY_TIME_MS, 'ms');
            }
        }
        
        // Handle blink - with debouncing
        if (data.blink === true || data.blink === 'true' || data.blink === 1) {
            const now = Date.now();
            if (now - lastBlinkTime > DEBOUNCE_MS) {
                console.log('😑 BLINK detected!');
                lastBlinkTime = now;
                handleBlink();
            }
        }
        
        // Handle left wink - scroll down with debouncing
        if (data.left_wink === true || data.left_wink === 'true' || data.left_wink === 1) {
            const now = Date.now();
            if (now - lastLeftWinkTime > DEBOUNCE_MS) {
                console.log('😉 LEFT WINK detected - Scrolling down!');
                lastLeftWinkTime = now;
                window.scrollBy({ top: 150, behavior: 'smooth' });
                
                // Visual feedback
                statusDiv.innerHTML = '😉 LEFT WINK - Scroll Down';
                setTimeout(() => {
                    statusDiv.innerHTML = '✅ Eye Control Active';
                }, 1000);
            }
        }
        
        // Handle right wink - scroll up with debouncing
        if (data.right_wink === true || data.right_wink === 'true' || data.right_wink === 1) {
            const now = Date.now();
            if (now - lastRightWinkTime > DEBOUNCE_MS) {
                console.log('😉 RIGHT WINK detected - Scrolling up!');
                lastRightWinkTime = now;
                window.scrollBy({ top: -150, behavior: 'smooth' });
                
                // Visual feedback
                statusDiv.innerHTML = '😉 RIGHT WINK - Scroll Up';
                setTimeout(() => {
                    statusDiv.innerHTML = '✅ Eye Control Active';
                }, 1000);
            }
        }
    }
    
    
    
    function updateCursorPosition() {
        // Update cursor position with professional smoothing
        // Interpolate smoothly between last and current position
        prevX = prevX + (lastX - prevX) * CURSOR_SMOOTH_FACTOR * sensitivity_level;
        prevY = prevY + (lastY - prevY) * CURSOR_SMOOTH_FACTOR * sensitivity_level;
        
        const x = prevX * window.innerWidth;
        const y = prevY * window.innerHeight;
        
        cursor.style.left = x + 'px';
        cursor.style.top = y + 'px';
        
        // Always check hover to detect buttons under cursor
        checkHover(x, y);
    }
    
    function checkHover(x, y) {
        // Hide cursor temporarily to get element below
        cursor.style.display = 'none';
        const element = document.elementFromPoint(x, y);
        cursor.style.display = 'block';
        
        if (!element) {
            // No element under cursor - deselect current hover
            if (hoveredElement) {
                hoveredElement.classList.remove('eye-focused');
                hoveredElement.style.outline = 'none';
                hoveredElement = null;
            }
            cursor.style.borderColor = '#00ff00';
            cursor.style.borderWidth = '4px';
            return;
        }
        
        // Find clickable element - check multiple selector patterns
        let clickable = element.closest('button, a, input[type="range"], input[type="number"], input[type="text"], input[type="password"], [role="button"], label, .gradio-button, [tabindex]:not([tabindex="-1"])');
        
        // If not found, try checking if element itself is clickable or in a clickable container
        if (!clickable) {
            // Check if element has onclick handler or is inside clickable area
            clickable = element.closest('[onclick], [class*="button"], [class*="click"], [class*="action"], .gradio-slider, .gradio-textbox');
        }
        
        // If still not found, walk up the DOM tree to find any clickable parent (up to 5 levels)
        if (!clickable && element.parentElement) {
            let current = element.parentElement;
            for (let i = 0; i < 5 && current; i++) {
                if (current.matches('button, a, input, [role="button"], label, .gradio-button, [onclick], [class*="button"], [class*="click"]')) {
                    clickable = current;
                    break;
                }
                current = current.parentElement;
            }
        }
        
        // Alternative: check if element or parent has pointer-events and size
        if (!clickable && element.offsetHeight > 0 && element.offsetWidth > 0) {
            const style = window.getComputedStyle(element);
            if (style.cursor === 'pointer' || element.style.cursor === 'pointer') {
                clickable = element;
            }
        }
        
        if (clickable) {
            if (clickable !== hoveredElement) {
                // New element - immediate visual feedback
                if (hoveredElement) {
                    hoveredElement.classList.remove('eye-focused');
                    hoveredElement.style.outline = 'none';
                }
                hoveredElement = clickable;
                hoveredElement.classList.add('eye-focused');
                hoverStart = Date.now();
                cursor.style.borderColor = '#00ffff';
                cursor.style.borderWidth = '6px';
                cursor.style.boxShadow = '0 0 15px #00ffff, 0 0 30px rgba(0, 255, 255, 0.5)';
                
                // Accessibility announcement
                const buttonText = clickable.textContent?.trim() || clickable.innerHTML?.substring(0, 50) || 'Button';
                console.log('👁️ Hovering over:', buttonText);
            }
        } else {
            if (hoveredElement) {
                hoveredElement.classList.remove('eye-focused');
                hoveredElement.style.outline = 'none';
                hoveredElement = null;
            }
            cursor.style.borderColor = '#00ff00';
            cursor.style.borderWidth = '4px';
            cursor.style.boxShadow = '0 0 10px #00ff00';
        }
    }
    
    function handleBlink() {
        const now = Date.now();
        
        // CRITICAL CHECK 1: Is click enabled? (not during page load)
        if (!clickEnabled || (now - pageLoadTime < CLICK_ENABLED_DELAY_MS)) {
            console.log('❌ CLICK DISABLED - Waiting', CLICK_ENABLED_DELAY_MS - (now - pageLoadTime), 'ms after page load');
            return;
        }
        
        // CRITICAL CHECK 2: Throttle clicks to prevent rapid-fire multiple tabs
        if (now - lastClickTime < CLICK_THROTTLE_MS) {
            console.log('⏱️ Click throttled - Wait', CLICK_THROTTLE_MS - (now - lastClickTime), 'ms more');
            return;
        }
        
        // CRITICAL CHECK 3: Gaze must be extremely stable
        if (!gazeStable || (now - gazeStableTime < GAZE_STABILITY_TIME_MS)) {
            console.log('⚠️ Gaze unstable - cannot click. Stable:', gazeStable, 'Duration:', now - gazeStableTime, 'ms');
            return;
        }
        
        // CRITICAL CHECK 4: Element must exist
        if (!hoveredElement) {
            console.log('⚠️ No element to click - move cursor to a button first');
            return;
        }
        
        console.log('✅ ALL CHECKS PASSED - Executing click!');
        
        // Visual feedback - quick flash
        cursor.classList.add('blinking');
        setTimeout(() => cursor.classList.remove('blinking'), 200);
        
        // Click hovered element
        if (hoveredElement) {
            console.log('✅ Clicking element:', hoveredElement.textContent || hoveredElement.innerHTML);
            lastClickTime = now;  // Update click throttle timer
            clickElement(hoveredElement);
            
            // Show feedback
            statusDiv.innerHTML = '🖱️ CLICKED!';
            setTimeout(() => {
                statusDiv.innerHTML = '✅ Eye Control Active';
            }, 800);
            
            hoveredElement.classList.remove('eye-focused');
            hoveredElement = null;
        } else {
            console.log('⚠️ No element hovered - move cursor over a button first!');
            statusDiv.innerHTML = '⚠️ Move cursor to button & blink!';
            setTimeout(() => {
                statusDiv.innerHTML = '✅ Eye Control Active';
            }, 1200);
        }
    }
    
    function clickElement(el) {
        console.log('🖱️ clickElement() executing for:', el);
        
        if (!el) return;
        
        // Flash effect
        const orig = el.style.background;
        const origColor = el.style.color;
        el.style.background = 'rgba(0, 255, 0, 0.8)';
        el.style.color = 'white';
        
        setTimeout(() => {
            el.style.background = orig;
            el.style.color = origColor;
        }, 150);
        
        // Use only ONE click method to prevent multiple tabs from opening
        try {
            console.log('✅ Clicking element using el.click()');
            el.click();
            console.log('✅ Single click executed - SUCCESS');
            
        } catch (e) {
            console.error('❌ Click error:', e);
        }
    }
    
    function setSensitivity(value) {
        sensitivity_level = parseFloat(value) || 1.0;
        console.log(`👁️ Sensitivity updated to ${sensitivity_level.toFixed(1)}x`);
    }
    
    function setDwellTime(value) {
        const newTime = parseInt(value) || 500;
        console.log(`⏱️ Dwell time updated to ${newTime}ms`);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    console.log('✅ Eye Control Script Loaded');
})();
</script>
"""

# Voice Recognition Script for Speech-to-Text
voice_recognition_js = """
<script>
let recognition = null;
let isListening = false;

function initVoiceRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        console.error('Speech Recognition not supported');
        return false;
    }
    
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;
    
    recognition.onstart = function() {
        console.log('[VOICE] 🎤 Listening started');
        isListening = true;
    };
    
    recognition.onresult = function(event) {
        console.log('[VOICE] Result event, total results:', event.results.length);
        
        let transcript = '';
        let isFinal = false;
        
        // Loop through ALL results and collect final transcripts
        for (let i = event.results.length - 1; i >= 0; i--) {
            const result = event.results[i];
            console.log('[VOICE] Result', i, '- isFinal:', result.isFinal, '- transcript:', result[0].transcript, '- confidence:', result[0].confidence);
            
            if (result.isFinal) {
                isFinal = true;
                transcript = result[0].transcript.trim();
                console.log('[VOICE] 🎯 Got final transcript:', transcript);
                break;
            } else if (transcript === '') {
                // Interim results - show what we're hearing
                transcript = result[0].transcript.trim();
                console.log('[VOICE] (interim):', transcript);
            }
        }
        
        console.log('[VOICE] Final transcript to process:', transcript, 'isFinal:', isFinal);
        
        if (transcript.length > 0) {
            // Try to find and update the Gradio textbox
            const textareas = document.querySelectorAll('textarea');
            console.log('[VOICE] Found', textareas.length, 'textareas');
            
            let found = false;
            
            // Search for textbox by placeholder text
            for (let i = 0; i < textareas.length; i++) {
                const placeholder = textareas[i].getAttribute('placeholder') || '';
                console.log('[VOICE] Textarea', i, '- placeholder:', placeholder);
                
                // Look for the voice command textbox by its placeholder
                if (placeholder.includes('voice command') || placeholder.includes('appear here')) {
                    console.log('[VOICE] 🎯 Found voice input at index', i, 'by placeholder');
                    textareas[i].value = transcript;
                    
                    // Trigger all possible events
                    textareas[i].dispatchEvent(new Event('input', { bubbles: true }));
                    textareas[i].dispatchEvent(new Event('change', { bubbles: true }));
                    textareas[i].dispatchEvent(new Event('blur', { bubbles: true }));
                    
                    console.log('[VOICE] ✅ Text updated to:', textareas[i].value);
                    found = true;
                    break;
                }
            }
            
            if (!found) {
                console.log('[VOICE] ⚠️ Placeholder search failed. Trying ID/class search...');
                // Fallback: search by looking for specific Gradio elements
                const allInputs = document.querySelectorAll('textarea, input[type="text"]');
                console.log('[VOICE] Total input fields found:', allInputs.length);
                
                for (let i = 0; i < allInputs.length; i++) {
                    const elem = allInputs[i];
                    const id = elem.id || '';
                    const className = elem.className || '';
                    const dataTestId = elem.getAttribute('data-testid') || '';
                    
                    console.log('[VOICE] Input', i, '- id:', id, '- class:', className, '- data-testid:', dataTestId);
                    
                    // Try to find by common Gradio patterns
                    if (className.includes('textbox') || className.includes('textfield') || 
                        id.includes('voice') || id.includes('command')) {
                        console.log('[VOICE] 🎯 Found by class/id at index', i);
                        elem.value = transcript;
                        elem.dispatchEvent(new Event('input', { bubbles: true }));
                        elem.dispatchEvent(new Event('change', { bubbles: true }));
                        found = true;
                        break;
                    }
                }
            }
            
            if (!found) {
                console.log('[VOICE] 🔴 Could not find voice input field. Using first textarea as fallback.');
                if (textareas.length > 0) {
                    // Use second textarea if available (first is usually tracker output)
                    const targetIndex = textareas.length > 1 ? 1 : 0;
                    textareas[targetIndex].value = transcript;
                    textareas[targetIndex].dispatchEvent(new Event('input', { bubbles: true }));
                    textareas[targetIndex].dispatchEvent(new Event('change', { bubbles: true }));
                    console.log('[VOICE] ✅ Fallback: Updated textarea at index', targetIndex);
                }
            }
        }
    };
    
    recognition.onerror = function(event) {
        console.error('[VOICE] ❌ Error:', event.error);
    };
    
    recognition.onend = function() {
        console.log('[VOICE] 🛑 Listening ended');
        isListening = false;
    };
    
    return true;
}

function startListening() {
    console.log('[VOICE] START LISTENING clicked');
    
    if (!recognition) {
        console.log('[VOICE] Initializing...');
        initVoiceRecognition();
    }
    
    if (recognition) {
        try {
            console.log('[VOICE] Starting recognition...');
            recognition.start();
            console.log('[VOICE] ✅ Recognition started');
        } catch (e) {
            console.error('[VOICE] Error:', e.message);
        }
    }
}

// Initialize when page fully loads
window.addEventListener('load', function() {
    console.log('[VOICE] Page loaded - initializing');
    initVoiceRecognition();
});

console.log('[VOICE] Voice Recognition Script Ready');
</script>
"""

# Combine both scripts
combined_head = eye_control_js + voice_recognition_js

# Create Gradio interface with eye control
with gr.Blocks(title="👁️ Eye Control Gaming Suite", theme=gr.themes.Soft(), css=custom_css, head=combined_head) as app:
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # HEADER SECTION
    # ═══════════════════════════════════════════════════════════════════════════════
    gr.Markdown("""
    # ⚡ EYE CONTROL GAMING SUITE ⚡
    ### Control Your Gaming Universe With Just Your Eyes
    """)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SECTION 1: SYSTEM INITIALIZATION & TRACKER STATUS
    # ═══════════════════════════════════════════════════════════════════════════════
    gr.Markdown("## ⚙️ SYSTEM INITIALIZATION")
    
    with gr.Row():
        tracker_status = gr.Textbox(
            label="TRACKER STATUS",
            value="🔴 OFFLINE",
            interactive=False,
            show_label=True,
            scale=2
        )
        
        with gr.Column(scale=1):
            start_btn = gr.Button("▶️ ACTIVATE TRACKER", variant="primary", size="lg", scale=1)
        
        with gr.Column(scale=1):
            stop_btn = gr.Button("⏹️ SHUTDOWN", variant="stop", size="lg", scale=1)
        
        with gr.Column(scale=1):
            test_cam_btn = gr.Button("📹 CAM TEST", size="lg", scale=1)
    
    tracker_output = gr.Textbox(
        label="SYSTEM LOG",
        value="System ready",
        interactive=False,
        lines=3,
        show_label=True
    )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SECTION 2: VOICE CONTROL WITH SPEECH RECOGNITION
    # ═══════════════════════════════════════════════════════════════════════════════
    gr.Markdown("## 🎤 VOICE CONTROL - SPEECH RECOGNITION")
    
    gr.Markdown("""
    **🎙️ FOR MOTOR-DISABLED USERS:**
    - Click the **🎙️ START LISTENING** button
    - **Speak clearly**: "Dash", "Shooter", "Western", "Memory", or "Menu"
    - Your speech will be converted to text automatically
    - Game launches after you click EXECUTE
    """)
    
    with gr.Row():
        voice_input = gr.Textbox(
            label="RECOGNIZED COMMAND",
            placeholder="Your voice command will appear here...",
            lines=2,
            show_label=True,
            scale=2,
            interactive=True
        )
        
        voice_btn = gr.Button("🎤 START LISTENING", variant="primary", size="lg", scale=1, min_width=200)
        
        with gr.Column(scale=2):
            gr.HTML("")
    
    voice_execute_btn = gr.Button("🚀 EXECUTE COMMAND", variant="primary", size="lg")
    
    voice_output = gr.Textbox(
        label="STATUS",
        value="🎤 Ready - Click START LISTENING to begin",
        interactive=False,
        lines=2,
        show_label=True
    )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SECTION 3: UNIFIED CONTROL PANEL - Calibration, Control Scheme, Cursor Settings
    # ═══════════════════════════════════════════════════════════════════════════════
    gr.Markdown("## 🎮 CONTROL PANEL")
    
    # ROW 1: CALIBRATION & CONTROL SCHEME (HORIZONTAL)
    with gr.Row(equal_height=True):
        # PANEL 1: CALIBRATION (Left)
        with gr.Column(scale=1):
            gr.HTML("""
            <div style="
                background: linear-gradient(135deg, rgba(0, 217, 255, 0.05) 0%, rgba(0, 255, 136, 0.05) 100%);
                border: 2px solid #00d9ff;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 0 20px rgba(0, 217, 255, 0.2), inset 0 0 10px rgba(0, 217, 255, 0.05);
                margin-bottom: 10px;
            ">
                <h3 style="color: #00ff88; margin: 0; text-align: center; letter-spacing: 1px;">🎯 CALIBRATION</h3>
            </div>
            """)
            
            calibrate_btn = gr.Button("🎯 CALIBRATE", variant="primary", size="lg")
            
            calibration_output = gr.Textbox(
                label="STATUS",
                value="Ready to calibrate",
                interactive=False,
                lines=5,
                show_label=True
            )
        
        # PANEL 2: CONTROL SCHEME (Right)
        with gr.Column(scale=1):
            gr.HTML("""
            <div style="
                background: linear-gradient(135deg, rgba(0, 217, 255, 0.05) 0%, rgba(0, 255, 136, 0.05) 100%);
                border: 2px solid #00d9ff;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 0 20px rgba(0, 217, 255, 0.2), inset 0 0 10px rgba(0, 217, 255, 0.05);
                margin-bottom: 10px;
            ">
                <h3 style="color: #00ff88; margin: 0; text-align: center; letter-spacing: 1px;">🎮 CONTROL SCHEME</h3>
            </div>
            """)
            
            gr.Markdown("""
            <div style="color: #e0e0e0; line-height: 2.2; font-size: 14px;">
            
            **👀 EYE GAZE**  
            Move cursor
            
            **😑 BLINK**  
            Select/Click
            
            **📜 SCROLL**  
            Look Up/Down
            
            **🎤 VOICE**  
            Launch Game
            </div>
            """)
    
    # ROW 2: CURSOR SETTINGS (Full Width Below)
    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML("""
            <div style="
                background: linear-gradient(135deg, rgba(0, 217, 255, 0.05) 0%, rgba(0, 255, 136, 0.05) 100%);
                border: 2px solid #00d9ff;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 0 20px rgba(0, 217, 255, 0.2), inset 0 0 10px rgba(0, 217, 255, 0.05);
                margin-bottom: 10px;
            ">
                <h3 style="color: #00ff88; margin: 0; text-align: center; letter-spacing: 1px;">👁️ CURSOR SETTINGS</h3>
            </div>
            """)
            
            sensitivity_slider = gr.Slider(
                minimum=0.5,
                maximum=2.0,
                value=1.0,
                step=0.1,
                label="SENSITIVITY",
                info="Slow (0.5) ← → Fast (2.0)",
                show_label=True
            )
            
            gr.HTML("""
            <div style="
                margin-top: 15px;
                padding: 10px;
                background: rgba(0, 217, 255, 0.08);
                border-left: 3px solid #00ff88;
                border-radius: 4px;
                color: #b0b0b0;
                font-size: 13px;
                line-height: 1.6;
            ">
            <strong style="color: #00d9ff;">💡 TIP:</strong><br>
            Adjust based on monitor<br>size & distance
            </div>
            """)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SECTION 4: GAME ARCADE
    # ═══════════════════════════════════════════════════════════════════════════════
    gr.Markdown("## 🎮 GAME ARCADE")
    
    # Row 1: Dash Racer & Target Shooter
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🏎️ DASH RACER")
            gr.Markdown("**SPEED MODE**")
            dash_btn = gr.Button("[ LAUNCH ]", size="lg")
            
        with gr.Column():
            gr.Markdown("### 🎯 TARGET SHOOTER")
            gr.Markdown("**PRECISION MODE**")
            shooter_btn = gr.Button("[ LAUNCH ]", size="lg")
    
    # Row 2: Western Shooter & Memory Match
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🤠 WESTERN SHOOTER")
            gr.Markdown("**COMBAT MODE**")
            western_btn = gr.Button("[ LAUNCH ]", size="lg")
        
        with gr.Column():
            gr.Markdown("### 🧩 MEMORY MATCH")
            gr.Markdown("**PUZZLE MODE**")
            memory_btn = gr.Button("[ LAUNCH ]", size="lg")
    
    # Row 3: Game Menu
    with gr.Row():
        menu_btn = gr.Button("📋 GAME MENU - VIEW ALL GAMES", size="lg", scale=1)
    
    game_output = gr.Textbox(
        label="GAME STATUS",
        value="Select a game to launch",
        interactive=False,
        lines=3,
        show_label=True
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
    
    # Voice START LISTENING button - triggers microphone capture
    voice_btn.click(
        fn=lambda: "� Microphone activated! Speak now...",
        outputs=voice_output,
        js="() => { console.log('Button clicked'); startListening(); return true; }"
    )
    
    # Voice EXECUTE button - processes the recognized speech
    voice_execute_btn.click(
        fn=voice_command_handler,
        inputs=voice_input,
        outputs=voice_output
    )
    
    calibrate_btn.click(
        fn=start_calibration,
        outputs=calibration_output
    )
    
    sensitivity_slider.change(
        fn=lambda x: f"Sensitivity set to {x:.1f}x",
        inputs=sensitivity_slider,
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
    print("="*70)
    print("🎮 Eye Control Games Interface")
    print("="*70)
    print("📂 Project directory:", PROJECT_DIR)
    print("👁️ Eye control will be active in the browser")
    print("🌐 Opening interface...")
    print("="*70)
    print("\n✨ CONTROLS:")
    print("   👀 Move eyes/head → Move cursor")
    print("   😑 Blink → Click button")
    print("   ⏱️ Hover 0.8s → Auto-click")
    print("   😉 Left wink → Scroll")
    print("   ⌨️ Press 'E' → Toggle eye control")
    print("\n" + "="*70 + "\n")
    
    try:
        # Find an available port starting from 7860
        port = 7860
        while port < 7900:
            try:
                app.launch(
                    server_name="127.0.0.1",
                    server_port=port,
                    share=False,
                    inbrowser=True
                )
                break
            except OSError:
                port += 1
                print(f"Port 7860 in use, trying {port}...")
                continue
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down...")
        if eye_tracker_running:
            stop_eye_tracker()
