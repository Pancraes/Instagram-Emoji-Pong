import numpy as np
import mss
import keyboard
import ctypes

X_START, Y_START = 1358, 31
X_END, Y_END = 1920, 970
WIDTH, HEIGHT = X_END - X_START, Y_END - Y_START
MOUSE_Y = 1000
CENTER_X = 1639
CENTER_Y = 1000

GRAY_MIN = 10
GRAY_MAX = 160
DIFF_TOL = 15

tracking = False
pending_mouse_down = False
program_running = True
spacebar_press_count = 0

sct = mss.mss()
monitor = {"top": Y_START, "left": X_START, "width": WIDTH, "height": HEIGHT}

def move_mouse(x, y):
    ctypes.windll.user32.SetCursorPos(x, y)

def mouse_down():
    ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)

def mouse_up():
    ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)

def on_enter():
    global tracking, program_running, spacebar_press_count, pending_mouse_down
    spacebar_press_count += 1
    if spacebar_press_count == 1:
        print("Started tracking.")
        move_mouse(CENTER_X, CENTER_Y)
        tracking = True
        pending_mouse_down = True
    elif spacebar_press_count == 2:
        print("Stopped tracking.")
        mouse_up()
        tracking = False
        program_running = False
        spacebar_press_count = 0

keyboard.add_hotkey('enter', on_enter)

print("Press ENTER to start/stop tracking.")

frame_count = 0
previous_raw_ball_x = None
direction = None

try:
    while program_running:
        if tracking:
            if pending_mouse_down:
                mouse_down()
                pending_mouse_down = False

            screenshot = sct.grab(monitor)
            img = np.array(screenshot)[:, :, :3]
            img_small = img[::2, ::2]

            r, g, b = img_small[:, :, 0], img_small[:, :, 1], img_small[:, :, 2]
            diff_rg = np.abs(r - g)
            diff_gb = np.abs(g - b)


            gray_mask = (
                (r >= GRAY_MIN) & (r <= GRAY_MAX) &
                (g >= GRAY_MIN) & (g <= GRAY_MAX) &
                (b >= GRAY_MIN) & (b <= GRAY_MAX) &
                (diff_rg < DIFF_TOL) & (diff_gb < DIFF_TOL)
            )

            ys, xs = np.where(gray_mask)

            if len(xs) > 100:
                median_x = int(np.median(xs)) * 2
                raw_ball_x = X_START + median_x

                if previous_raw_ball_x is not None:
                    if raw_ball_x > previous_raw_ball_x:
                        new_direction = 'right'
                    elif raw_ball_x < previous_raw_ball_x:
                        new_direction = 'left'
                    else:
                        new_direction = direction

                    if new_direction != direction:
                        direction = new_direction

                offset = 0
                if direction == 'left':
                    offset = -75
                elif direction == 'right':
                    offset = 75

                final_x = raw_ball_x + offset
                final_x = max(X_START, min(final_x, X_END))

                move_mouse(final_x, MOUSE_Y)
                previous_raw_ball_x = raw_ball_x

            frame_count += 1
            if frame_count % 30 == 0:
                print(f"[Debug] Ball pixels: {len(xs)} | Direction: {direction}")

except KeyboardInterrupt:
    print("Stopped by user.")
