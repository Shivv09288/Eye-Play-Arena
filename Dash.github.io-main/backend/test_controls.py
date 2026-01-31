"""
Quick test to verify keyboard controls work with the game
"""
import pyautogui
import time

pyautogui.PAUSE = 0.01
pyautogui.FAILSAFE = False

print("=" * 60)
print("🧪 Testing Keyboard Controls")
print("=" * 60)
print("\nThis will test if keyboard commands reach the game.")
print("\n⚠️  CLICK ON THE GAME WINDOW NOW!")
print("Starting in 3 seconds...\n")

for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)

print("\n✅ Starting tests:\n")

# Test 1: Start game
print("Test 1: Pressing 'C' to start game...")
pyautogui.press('c')
time.sleep(2)

# Test 2: Accelerate
print("Test 2: Pressing UP arrow (accelerate)...")
pyautogui.keyDown('up')
time.sleep(2)
pyautogui.keyUp('up')
time.sleep(1)

# Test 3: Left
print("Test 3: Pressing LEFT arrow...")
pyautogui.keyDown('left')
time.sleep(1)
pyautogui.keyUp('left')
time.sleep(0.5)

# Test 4: Right
print("Test 4: Pressing RIGHT arrow...")
pyautogui.keyDown('right')
time.sleep(1)
pyautogui.keyUp('right')
time.sleep(0.5)

# Test 5: Combined
print("Test 5: Accelerate + Steer LEFT...")
pyautogui.keyDown('up')
pyautogui.keyDown('left')
time.sleep(2)
pyautogui.keyUp('left')
pyautogui.keyUp('up')

print("\n✅ Test complete!")
print("\nDid you see the car move in the game?")
print("If YES - eye tracking should work")
print("If NO - make sure the game window is in focus")
