# Eye Control Gaming Suite

An innovative gaming platform that enables hands-free control of games using eye tracking technology. This project combines computer vision with interactive game experiences to provide an accessible and futuristic gaming interface.

## 🎮 Features

- **Eye-Controlled Gaming** - Control games using only your eyes
- **Multiple Game Modes**
  - Memory Game - Test your memory with eye-controlled card matching
  - Shooting Game - Shoot targets using eye tracking
  - Western Shooter - An immersive western-themed shooting game
- **Real-time Eye Tracking** - Uses advanced computer vision for accurate eye detection
- **WebSocket Communication** - Real-time data transmission between frontend and backend
- **Voice Control Integration** - Voice command support for game interactions
- **User System** - User profile management and game history
- **Gradio Interface** - Interactive demo interface for testing eye control features

## 📁 Project Structure

```
Eye-Control-Gaming-Suite/
├── backend/
│   ├── backend_server.py          # Main backend server
│   ├── eye_controller.py          # Eye tracking control logic
│   ├── eye_websocket_server.py    # WebSocket server for real-time communication
│   ├── gradio_app.py              # Gradio application interface
│   ├── gradio_eye_control.py      # Eye control Gradio demo
│   ├── run_demo.py                # Demo runner script
│   ├── test_controls.py           # Eye control tests
│   ├── test_websocket.py          # WebSocket tests
│   └── backend_requirements.txt    # Backend dependencies
│
├── frontend/
│   ├── index.html                 # Main landing page
│   ├── index_eye_control.html     # Eye control interface
│   ├── game_menu.html             # Game selection menu
│   ├── memory_game.html           # Memory game interface
│   ├── shooting_game.html         # Shooting game interface
│   ├── western_shooter.html       # Western shooter game
│   ├── voice_control_test.html    # Voice control testing page
│   ├── user_system.js             # User management system
│   └── javascript/
│       ├── 1.js                   # Game logic and utilities
│       └── null.js                # Additional utilities
│
├── images/
│   └── birds/                     # Game assets and images
│
├── requirements.txt               # Main project dependencies
├── backend_requirements.txt        # Backend-specific dependencies
└── README.md                      # This file
```

 🚀 Getting Started

Prerequisites

- Python 3.8 or higher
- A webcam or eye-tracking device
- Modern web browser (Chrome, Firefox, Edge)
- Git

 Installation

1. Clone the repository
   ```bash
   git clone https://github.com/Shivv09288/Eye-Play-Arena.git
   cd Eye-Play-Arena
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   pip install -r backend/backend_requirements.txt
   ```

3. **Set up virtual environment (optional but recommended)**
   ```bash
   python -m venv env
   # On Windows:
   env\Scripts\activate
   # On macOS/Linux:
   source env/bin/activate
   ```

### Running the Application

#### Backend Server
```bash
cd backend
python backend_server.py
```

#### Eye WebSocket Server
```bash
cd backend
python eye_websocket_server.py
```

#### Gradio Demo Interface
```bash
cd backend
python gradio_app.py
```

#### Frontend
Open `frontend/index.html` in your web browser or run a local server:
```bash
# Using Python 3
python -m http.server 8000
# Then visit: http://localhost:8000/frontend/
```

## 🎯 Usage

### Playing a Game

1. Navigate to the **Game Menu** (`game_menu.html`)
2. Select your desired game:
   - **Memory Game**: Match pairs using eye gaze
   - **Shooting Game**: Aim and shoot targets with your eyes
   - **Western Shooter**: Engage in a western-themed shooting experience
3. Follow the on-screen instructions
4. Use your eye movements to control gameplay

### Eye Tracking Setup

1. Open `index_eye_control.html`
2. Allow camera access when prompted
3. Calibrate your eye position by looking at marked points on the screen
4. Start using eye control across the platform

### Voice Control

1. Visit `voice_control_test.html`
2. Enable microphone access
3. Speak commands to control game actions (voice commands vary by game)

## 🛠️ Technologies Used

- **Backend**
  - Python 3.x
  - Flask / FastAPI (Web server)
  - OpenCV (Computer Vision)
  - WebSocket (Real-time communication)
  - Gradio (Demo interface)

- **Frontend**
  - HTML5
  - CSS3
  - JavaScript (Vanilla & Libraries)
  - WebSocket API
  - Web Audio API (Voice control)

- **Eye Tracking**
  - Dlib (Face & eye detection)
  - MediaPipe (Alternative face detection)
  - NumPy (Numerical computations)

## 📋 System Requirements

- **CPU**: Intel i5 or equivalent
- **RAM**: 4GB minimum (8GB recommended)
- **Webcam**: 720p or higher resolution
- **Internet**: Stable connection for WebSocket communication

## 🧪 Testing

Run the test scripts to verify functionality:

```bash
# Test eye control
python backend/test_controls.py

# Test WebSocket connection
python backend/test_websocket.py
```

## 📝 Configuration

Key configuration files:
- `backend_requirements.txt` - Python dependencies
- `requirements.txt` - Main project requirements
- `backend/gradio_app.py` - Gradio interface settings
- `frontend/user_system.js` - User system configuration

## 🐛 Troubleshooting

### Webcam not detected
- Ensure your webcam is properly connected
- Check browser permissions for camera access
- Try a different USB port if using external webcam

### Eye tracking inaccurate
- Ensure proper lighting conditions
- Clean your webcam lens
- Recalibrate the eye tracking system
- Adjust camera position for better face detection

### WebSocket connection failed
- Verify backend server is running
- Check firewall settings
- Ensure correct server URL in frontend

## 🤝 Contributing

Contributions are welcome! Feel free to:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**Shiva Prasad K**
- GitHub: [@Shivv09288](https://github.com/Shivv09288)
- Email: shivv9341@gmail.com

## 🙏 Acknowledgments

- OpenCV community for computer vision libraries
- Dlib for face and eye detection
- MediaPipe for alternative detection models
- All contributors and testers

## 📞 Support

For support, email shivv9341@gmail.com or open an issue on GitHub.

---

**Made with ❤️ by Shiva Prasad K**
