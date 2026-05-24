import time
import random
import pydirectinput
import pyautogui
import pytesseract
import cv2
import numpy as np

# --- CONFIGURATION ---
# IMPORTANT: Ensure this path points to where you installed Tesseract-OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Your exact custom 1920x1080 measurements
AFK_TEXT_REGION = (700, 320, 520, 100)  # The "ARE YOU STILL THERE?" box
AFK_KEY_AREA = (649, 420, 537, 144)  # The wide area where the keycap travels
ERROR_TEXT_REGION = (800, 440, 320, 80)  # The "Wrong Button!" penalty text


def check_for_afk_prompt():
    """Looks for the main AFK check text, applying thresholding to delete the translucent background."""
    screenshot = pyautogui.screenshot(region=AFK_TEXT_REGION)
    gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    # Turn the pure white text black, and wipe out the translucent background
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    text = pytesseract.image_to_string(thresh).upper()
    return "STILL" in text or "THERE" in text


def check_for_error():
    """Looks for the red penalty text after a misclick."""
    screenshot = pyautogui.screenshot(region=ERROR_TEXT_REGION)
    gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    text = pytesseract.image_to_string(gray).upper()
    return "WRONG" in text or "BUTTON" in text


def get_afk_key():
    """Finds the keycap, isolates the letter using Center-Gravity, smooths, and reads it."""
    screenshot = pyautogui.screenshot(region=AFK_KEY_AREA)
    img = np.array(screenshot)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Turn keycap white, background black
    _, thresh = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        # --- THE SHAPE PROFILE FILTER ---
        # 1. Calculate Aspect Ratio (Width divided by Height). Squares are ~1.0.
        aspect_ratio = float(w) / float(h)

        # 2. Size Limits: Must be bigger than 30px (ignores mouse cursor/dust)
        #                 Must be smaller than 150px (ignores giant banners/signs)
        # 3. Shape Limit: Aspect ratio must be between 0.8 and 2.5 (ignores long horizontal bars)
        if (30 < w < 150) and (30 < h < 150) and (0.8 < aspect_ratio < 2.5):

            cropped_keycap = thresh[y:y + h, x:x + w]

            # --- THE 4-WAY CHOP ---
            # Chop 38% top (hardhat), 10% bottom (shadow)
            # Chop 25% left (heavy shadow), 10% right (margin)
            startY, endY = int(h * 0.38), int(h * 0.90)
            startX, endX = int(w * 0.25), int(w * 0.90)
            clean_keycap = cropped_keycap[startY:endY, startX:endX]

            inv_cap = cv2.bitwise_not(clean_keycap)
            inner_contours, _ = cv2.findContours(inv_cap, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Find the true center of our chopped image
            ch, cw = inv_cap.shape
            center_x, center_y = cw // 2, ch // 2

            all_x, all_y, all_xw, all_yh = [], [], [], []

            for icnt in inner_contours:
                ix, iy, iw, ih = cv2.boundingRect(icnt)

                # Ignore microscopic dust
                if iw > 4 and ih > 6:
                    # Find the center of this specific shape
                    shape_cx = ix + (iw // 2)
                    shape_cy = iy + (ih // 2)

                    # --- THE CENTER GRAVITY FILTER ---
                    # Only accept this shape if its center is reasonably close to the middle.
                    if abs(shape_cx - center_x) < (cw * 0.40) and abs(shape_cy - center_y) < (ch * 0.40):
                        all_x.append(ix)
                        all_y.append(iy)
                        all_xw.append(ix + iw)
                        all_yh.append(iy + ih)

            # If we successfully found valid, centered letter parts
            if all_x:
                min_x, min_y = min(all_x), min(all_y)
                max_xw, max_yh = max(all_xw), max(all_yh)

                letter_crop = clean_keycap[min_y:max_yh, min_x:max_xw]

                # --- ANTI-ALIASING & SMOOTHING ---
                # Upscale by 500% to create a massive canvas
                final_img = cv2.resize(letter_crop, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)

                # Gaussian Blur to melt the jagged 8-bit edges together
                final_img = cv2.GaussianBlur(final_img, (5, 5), 0)

                # Re-threshold to snap the blurry edges back to crisp font lines
                _, final_img = cv2.threshold(final_img, 150, 255, cv2.THRESH_BINARY)

                # Add a massive 50px pure white border so Tesseract has breathing room
                final_img = cv2.copyMakeBorder(final_img, 50, 50, 50, 50, cv2.BORDER_CONSTANT, value=[255, 255, 255])

                # Overwrite this file so you can always check what the bot is reading
                cv2.imwrite("debug_cropped_key.png", final_img)

                # PSM 8 (Single Word) handles these massive, smoothed images best
                config = '--psm 8 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz'
                char = pytesseract.image_to_string(final_img, config=config).strip().lower()
                clean_char = ''.join(filter(str.isalpha, char))

                if len(clean_char) == 1:
                    return clean_char

    return None


# --- MAIN LOOP ---
print("Starting in 5 seconds. Please tab into Tower Unite...")
time.sleep(5)
print("Bot running. Press CTRL+C in this console to stop.")

afk_lock = False
failsafe_counter = 0

try:
    while True:
        # If we see the prompt OR the spacebar lock is active, enter solving mode
        if check_for_afk_prompt() or afk_lock:

            if not afk_lock:
                print("\n*** AFK Check Detected! Locking Spacebar... ***")
                afk_lock = True
                time.sleep(0.5)

            key_to_press = get_afk_key()

            if key_to_press:
                print(f"Pressing key: {key_to_press}")
                pydirectinput.press(key_to_press)
                time.sleep(1.5)

                if check_for_error():
                    print("Misclick detected! Waiting 3.5 seconds penalty...")
                    time.sleep(3.5)
                else:
                    print("Success! Unlocking Spacebar...")
                    afk_lock = False
                    failsafe_counter = 0
                    time.sleep(1)
            else:
                print("Could not isolate a valid letter. Retrying... (Spacebar is locked)")
                failsafe_counter += 1

                # If it gets stuck reading a completely broken frame for 10 seconds, reset it.
                if failsafe_counter >= 10:
                    print("Failsafe Triggered: Unlocking spacebar to prevent freezing.")
                    afk_lock = False
                    failsafe_counter = 0

                time.sleep(1)
        else:
            pydirectinput.press('space')

            # --- THE SMART SLEEP ---
            delay = random.uniform(2.5, 3.0)
            print(f"Spun slot. Waiting {delay:.2f} seconds...")

            wait_start_time = time.time()

            # Keep looping until the total randomized delay time has passed
            while (time.time() - wait_start_time) < delay:
                # Rapid-fire peek to see if the AFK check appeared mid-spin
                if check_for_afk_prompt():
                    print("\n*** Prompt detected mid-spin! Interrupting wait... ***")
                    afk_lock = True
                    break  # Instantly break out of this waiting loop and solve the check

                # Sleep in tiny chunks to keep CPU usage low while remaining highly responsive
                time.sleep(0.25)

except KeyboardInterrupt:
    print("\nBot stopped by user.")