import pyautogui
import time
from PIL import ImageGrab
import keyboard  # For global hotkey
import numpy as np  # For fast image processing

# Coordinates for ball detection rectangle
X_START, Y_START = 1358, 31
X_END, Y_END = 1920, 980  # Quick fix: avoid bottom black surface

MOUSE_Y = 1000  # fixed Y position for mouse

# Color tolerance for black detection
BLACK_RGB = (0, 0, 0)
TOLERANCE = 80  # Loosened: Accept colors with RGB values close to black within this range

tracking = False  # Whether tracking is active
mouse_x = (X_START + X_END) // 2  # Start mouse X in middle
program_running = True
pending_mouse_down = False


def is_black_with_tolerance(color):
    r, g, b = color
    return r <= TOLERANCE and g <= TOLERANCE and b <= TOLERANCE

def is_isolated_black(screen, x, y):
    # Check if the black pixel is not part of a long horizontal line (robust fix)
    width, height = screen.size
    count = 0
    for dx in range(-3, 4):  # check 3 pixels left/right
        nx = x + dx
        if 0 <= nx < width:
            if is_black_with_tolerance(screen.getpixel((nx, y))):
                count += 1
    return count <= 3  # Only consider as ball if not part of a line


print("Press ENTER to start tracking and hold mouse down.\nPress ENTER again to stop and exit.")

spacebar_press_count = 0

CENTER_X = 1639
CENTER_Y = 1000

def on_enter():
    global tracking, program_running, spacebar_press_count, pending_mouse_down
    spacebar_press_count += 1
    if spacebar_press_count == 1:
        print("Starting tracking and holding mouse down.")
        pyautogui.moveTo(CENTER_X, CENTER_Y)
        tracking = True
        pending_mouse_down = True
    elif spacebar_press_count == 2:
        print("Stopping tracking, releasing mouse, and exiting program.")
        pyautogui.mouseUp()
        tracking = False
        program_running = False

# Register the global hotkey for Enter
keyboard.add_hotkey('enter', on_enter)

try:
    while program_running:
        if tracking:
            if pending_mouse_down:
                print("Calling pyautogui.mouseDown()...")
                pending_mouse_down = False
            # Capture the rectangle where ball may appear
            screen = ImageGrab.grab(bbox=(X_START, Y_START, X_END, Y_END))
            ball_pos = None
            width, height = screen.size

            # Convert image to numpy array for fast processing
            img_np = np.array(screen)
            if img_np.shape[2] == 4:
                img_np = img_np[:, :, :3]  # Drop alpha if present

            r = img_np[:, :, 0]
            g = img_np[:, :, 1]
            b = img_np[:, :, 2]

            # Ball gray mask
            ball_mask = (
                (r >= 20) & (r <= 130) &
                (g >= 20) & (g <= 130) &
                (b >= 20) & (b <= 130) &
                (np.abs(r - g) < 10) & (np.abs(g - b) < 10) & (np.abs(b - r) < 10)
            )
            # Exclude bottom 40px to avoid the platform
            ball_mask[-40:, :] = False

            ys, xs = np.where(ball_mask)
            print(f"Found {len(xs)} ball pixels this frame (numpy fast).")
            if len(xs) > 200:
                avg_x = int(xs.mean())
                ball_x = X_START + avg_x
                ball_pos = (ball_x, MOUSE_Y)
                print(f"Detected ball X at: {ball_x}")
            else:
                print("No ball detected.")

            if ball_pos:
                pyautogui.moveTo(ball_pos[0], ball_pos[1])
                print(f"Moved mouse to: ({ball_pos[0]}, {ball_pos[1]}) and quick down/up.")


        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nProgram stopped.")
