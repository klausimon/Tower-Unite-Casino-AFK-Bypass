import time
import random
import pydirectinput
import pyautogui
import pytesseract
import cv2
import numpy as np

# --- CONFIGURATION ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Your exact custom 1920x1080 measurements
AFK_TEXT_REGION = (700, 320, 520, 100)
AFK_KEY_AREA = (649, 420, 537, 144)
ERROR_TEXT_REGION = (800, 440, 320, 80)


def check_for_afk_prompt():
    screenshot = pyautogui.screenshot(region=AFK_TEXT_REGION)
    gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    cv2.imwrite("debug_text_vision.png", gray)
    text = pytesseract.image_to_string(gray).upper()
    return "STILL" in text or "THERE" in text


def check_for_error():
    screenshot = pyautogui.screenshot(region=ERROR_TEXT_REGION)
    gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    text = pytesseract.image_to_string(gray).upper()
    return "WRONG" in text or "BUTTON" in text


def get_afk_key():
    screenshot = pyautogui.screenshot(region=AFK_KEY_AREA)
    img = np.array(screenshot)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # 1. Turn keycap white, background black
    _, thresh = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY)
    cv2.imwrite("debug_keycap_full_area.png", thresh)

    # 2. Find the main keycap
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        # Filter out mouse cursor
        if w > 30 and h > 30:
            cropped_keycap = thresh[y:y + h, x:x + w]

            # --- THE 4-WAY CHOP ---
            startY, startX = int(h * 0.40), int(w * 0.25)
            endX = int(w * 0.85)
            clean_keycap = cropped_keycap[startY:h, startX:endX]

            # --- NEW: THE LETTER HUNTER ---
            # Invert the image so the letter becomes WHITE and background becomes BLACK
            inv_cap = cv2.bitwise_not(clean_keycap)

            # Find the shapes (the letter + the noise) inside our chopped image
            inner_contours, _ = cv2.findContours(inv_cap, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            ch, cw = inv_cap.shape  # Get height and width of this small image

            for icnt in inner_contours:
                ix, iy, iw, ih = cv2.boundingRect(icnt)

                # MATHEMATICAL FILTER:
                # If the shape touches the outer 2 pixels of the image, it is noise! Ignore it.
                if ix > 2 and iy > 2 and (ix + iw) < (cw - 2) and (iy + ih) < (ch - 2):

                    # Also make sure it's not a tiny speck of dust (must be > 5x5 pixels)
                    if iw > 5 and ih > 5:

                        # We found the true letter! Crop it out exactly.
                        letter_crop = clean_keycap[iy:iy + ih, ix:ix + iw]

                        # --- THE MAGNIFYING GLASS ---
                        # Upscale by 400%
                        final_img = cv2.resize(letter_crop, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)

                        # Add a massive 40px pure white border around it
                        final_img = cv2.copyMakeBorder(final_img, 40, 40, 40, 40, cv2.BORDER_CONSTANT,
                                                       value=[255, 255, 255])

                        # Check this image! It should be literally nothing but the letter.
                        cv2.imwrite("debug_cropped_key.png", final_img)

                        config = '--psm 10 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz'
                        char = pytesseract.image_to_string(final_img, config=config).strip().lower()

                        if len(char) == 1 and char.isalpha():
                            return char

    return None


# --- MAIN LOOP ---
print("Starting in 5 seconds. Please tab into Tower Unite...")
time.sleep(5)
print("Bot running. Press CTRL+C in this console to stop.")

try:
    while True:
        if check_for_afk_prompt():
            print("\n*** AFK Check Detected! ***")
            time.sleep(0.5)

            key_to_press = get_afk_key()

            if key_to_press:
                print(f"Pressing key: {key_to_press}")
                pydirectinput.press(key_to_press)
                time.sleep(1)

                if check_for_error():
                    print("Misclick detected! Waiting 3.5 seconds penalty...")
                    time.sleep(3.5)
                else:
                    print("Success! Resuming...")
                    time.sleep(1)
            else:
                print("Could not isolate a valid letter. Retrying next loop...")
                time.sleep(1)
        else:
            pydirectinput.press('space')
            delay = random.uniform(2.0, 3.0)
            print(f"Spun slot. Waiting {delay:.2f} seconds...")
            time.sleep(delay)

except KeyboardInterrupt:
    print("\nBot stopped by user.")