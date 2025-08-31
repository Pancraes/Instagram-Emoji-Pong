import pyautogui
import time
from PIL import ImageGrab
import keyboard
import numpy as np

X_START, Y_START = 1358, 31
X_END, Y_END = 1920, 980

MOUSE_Y = 1000

BLACK_RGB = (0, 0, 0)
TOLERANCE = 80  

tracking = False 
mouse_x = (X_START + X_END) // 2
program_running = True
pending_mouse_down = False


def is_black_with_tolerance(color):
    r, g, b = color
    return r <= TOLERANCE and g <= TOLERANCE and b <= TOLERANCE

def is_isolated_black(screen, x, y):
    width, height = screen.size
    count = 0
    for dx in range(-3, 4):
        nx = x + dx
        if 0 <= nx < width:
            if is_black_with_tolerance(screen.getpixel((nx, y))):
                count += 1
    return count <= 3


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

keyboard.add_hotkey('enter', on_enter)

try:
    while program_running:
        if tracking:
            if pending_mouse_down:
                print("Calling pyautogui.mouseDown()...")
                pending_mouse_down = False
            screen = ImageGrab.grab(bbox=(X_START, Y_START, X_END, Y_END))
            ball_pos = None
            width, height = screen.size

            img_np = np.array(screen)
            if img_np.shape[2] == 4:
                img_np = img_np[:, :, :3]

            r = img_np[:, :, 0]
            g = img_np[:, :, 1]
            b = img_np[:, :, 2]

            ball_mask = (
                (r >= 20) & (r <= 130) &
                (g >= 20) & (g <= 130) &
                (b >= 20) & (b <= 130) &
                (np.abs(r - g) < 10) & (np.abs(g - b) < 10) & (np.abs(b - r) < 10)
            )
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

except KeyboardInterrupt:
    print("\nProgram stopped.")