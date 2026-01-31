/**
 * Shared User System for Eye Control Games
 * Provides username entry modal and MongoDB integration for all games
 */

const BACKEND_URL = 'http://localhost:5000';
let currentUser = null;
let currentGameType = 'unknown';

/**
 * Initialize the user system
 * @param {string} gameType - Type of game (dash_racer, target_shooter, western_shooter, memory_match)
 */
function initUserSystem(gameType) {
    currentGameType = gameType;
    
    // Create and inject the username modal HTML
    const modalHTML = `
        <div id="username-modal" class="user-modal">
            <div class="user-modal-content">
                <h2 class="user-modal-title">👁️ Eye Control Games</h2>
                <p class="user-modal-subtitle">Enter your name to save scores</p>
                <input 
                    type="text" 
                    id="username-input" 
                    class="user-input" 
                    placeholder="Your Name" 
                    maxlength="20"
                    autocomplete="off"
                />
                <div id="username-error" class="user-error"></div>
                <button id="username-submit" class="user-button">START GAME</button>
                <button id="skip-login" class="user-button-secondary">Skip (Play as Guest)</button>
            </div>
        </div>

        <!-- User Info Display (top-right corner) -->
        <div id="user-info-display" class="user-info" style="display: none;">
            <div class="user-info-name">👤 <span id="username-display">Guest</span></div>
            <div class="user-info-stats">
                🏆 High: <span id="user-highscore">0</span> | 
                🎮 Games: <span id="user-games">0</span>
            </div>
        </div>
    `;
    
    // Inject modal into body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add styles
    addUserSystemStyles();
    
    // Set up event listeners
    setupEventListeners();
    
    // Show modal on load
    showUsernameModal();
}

/**
 * Add CSS styles for the user system
 */
function addUserSystemStyles() {
    const styles = `
        <style id="user-system-styles">
            .user-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.95);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
                font-family: "Press Start 2P", monospace;
            }

            .user-modal.hidden {
                display: none;
            }

            .user-modal-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px;
                border-radius: 20px;
                border: 4px solid #FFD700;
                text-align: center;
                max-width: 500px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            }

            .user-modal-title {
                font-size: 24px;
                color: #FFD700;
                margin-bottom: 15px;
                text-shadow: 3px 3px 0 rgba(0, 0, 0, 0.5);
            }

            .user-modal-subtitle {
                font-size: 12px;
                color: white;
                margin-bottom: 25px;
                line-height: 1.6;
            }

            .user-input {
                width: 100%;
                padding: 15px;
                font-family: "Press Start 2P", monospace;
                font-size: 14px;
                border: 3px solid #FFD700;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.9);
                text-align: center;
                margin-bottom: 10px;
                outline: none;
            }

            .user-input:focus {
                background: white;
                box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
            }

            .user-error {
                color: #ff6b6b;
                font-size: 10px;
                min-height: 20px;
                margin-bottom: 10px;
            }

            .user-button {
                width: 100%;
                padding: 15px;
                font-family: "Press Start 2P", monospace;
                font-size: 14px;
                background: #FFD700;
                color: #000;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.3s;
                margin-bottom: 10px;
            }

            .user-button:hover {
                background: #FFA500;
                transform: scale(1.05);
            }

            .user-button:disabled {
                background: #666;
                color: #999;
                cursor: not-allowed;
                transform: none;
            }

            .user-button-secondary {
                width: 100%;
                padding: 12px;
                font-family: "Press Start 2P", monospace;
                font-size: 10px;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.3s;
            }

            .user-button-secondary:hover {
                background: rgba(255, 255, 255, 0.3);
                border-color: rgba(255, 255, 255, 0.5);
            }

            .user-info {
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(0, 0, 0, 0.7);
                padding: 15px;
                border-radius: 10px;
                border: 3px solid #FFD700;
                color: white;
                font-family: "Press Start 2P", monospace;
                font-size: 10px;
                text-align: right;
                z-index: 9999;
                text-shadow: 2px 2px 0 rgba(0, 0, 0, 0.8);
            }

            .user-info-name {
                margin-bottom: 8px;
                color: #FFD700;
                font-size: 11px;
            }

            .user-info-stats {
                color: #fff;
            }
        </style>
    `;
    
    document.head.insertAdjacentHTML('beforeend', styles);
}

/**
 * Set up event listeners for the user system
 */
function setupEventListeners() {
    const submitBtn = document.getElementById('username-submit');
    const skipBtn = document.getElementById('skip-login');
    const usernameInput = document.getElementById('username-input');
    
    // Submit username
    submitBtn.addEventListener('click', handleUsernameSubmit);
    
    // Skip login (play as guest)
    skipBtn.addEventListener('click', () => {
        hideUsernameModal();
        showUserInfo(false);
    });
    
    // Allow Enter key to submit
    usernameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleUsernameSubmit();
        }
    });
    
    // AUTO-SKIP FOR ACCESSIBILITY: Auto-skip login after 5 seconds if user hasn't interacted
    let autoSkipTimer = null;
    let userInteracted = false;
    
    const resetAutoSkip = () => {
        userInteracted = true;
        if (autoSkipTimer) clearTimeout(autoSkipTimer);
    };
    
    usernameInput.addEventListener('input', resetAutoSkip);
    submitBtn.addEventListener('click', resetAutoSkip);
    
    // Show the username modal which will trigger auto-skip
    setTimeout(() => {
        if (!userInteracted) {
            autoSkipTimer = setTimeout(() => {
                if (!userInteracted) {
                    console.log('⏱️ Auto-skipping login dialog for accessibility (no interaction detected)');
                    hideUsernameModal();
                    showUserInfo(false);
                }
            }, 5000); // Auto-skip after 5 seconds
        }
    }, 500);
}

/**
 * Handle username submission
 */
async function handleUsernameSubmit() {
    const username = document.getElementById('username-input').value.trim();
    const errorEl = document.getElementById('username-error');
    const submitBtn = document.getElementById('username-submit');
    
    if (!username) {
        errorEl.textContent = 'Please enter your name';
        return;
    }
    
    submitBtn.disabled = true;
    errorEl.textContent = 'Connecting...';
    errorEl.style.color = '#FFD700';
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/user/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = data.user;
            
            // Update UI
            document.getElementById('username-display').textContent = currentUser.username;
            
            // Get game-specific high score if available
            const gameStats = currentUser.game_stats || {};
            const thisGameStats = gameStats[currentGameType] || { high_score: 0, games_played: 0 };
            
            document.getElementById('user-highscore').textContent = thisGameStats.high_score;
            document.getElementById('user-games').textContent = thisGameStats.games_played;
            
            hideUsernameModal();
            showUserInfo(true);
            
            console.log('✅ User logged in:', currentUser);
        } else {
            errorEl.textContent = data.error || 'Failed to login';
            errorEl.style.color = '#ff6b6b';
            submitBtn.disabled = false;
        }
    } catch (error) {
        console.error('Failed to connect to server:', error);
        errorEl.textContent = 'Server offline. Playing as guest.';
        errorEl.style.color = '#FFA500';
        
        setTimeout(() => {
            hideUsernameModal();
            showUserInfo(false);
        }, 2000);
    }
}

/**
 * Show username modal
 */
function showUsernameModal() {
    document.getElementById('username-modal').classList.remove('hidden');
    document.getElementById('username-input').focus();
}

/**
 * Hide username modal
 */
function hideUsernameModal() {
    document.getElementById('username-modal').classList.add('hidden');
}

/**
 * Show/hide user info display
 */
function showUserInfo(show) {
    document.getElementById('user-info-display').style.display = show ? 'block' : 'none';
}

/**
 * Save score to MongoDB
 * @param {number} score - The score to save
 * @param {object} options - Additional options (lapTime, stats, etc.)
 */
async function saveScore(score, options = {}) {
    if (!currentUser) {
        console.log('No user logged in, score not saved');
        return { success: false, reason: 'not_logged_in' };
    }
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/score/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: currentUser.username,
                game_type: currentGameType,
                score: score,
                lap_time: options.lapTime || '',
                stats: options.stats || {}
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Score saved:', data);
            
            // Update display
            if (data.game_high_score !== undefined) {
                document.getElementById('user-highscore').textContent = data.game_high_score;
            }
            if (data.games_played_this_type !== undefined) {
                document.getElementById('user-games').textContent = data.games_played_this_type;
            }
            
            return {
                success: true,
                isNewHighScore: data.is_new_high_score,
                gameHighScore: data.game_high_score,
                totalGames: data.games_played_this_type
            };
        }
        
        return { success: false, reason: 'server_error' };
        
    } catch (error) {
        console.error('Failed to save score:', error);
        return { success: false, reason: 'network_error' };
    }
}

/**
 * Get current user
 */
function getCurrentUser() {
    return currentUser;
}

/**
 * Check if user is logged in
 */
function isUserLoggedIn() {
    return currentUser !== null;
}
