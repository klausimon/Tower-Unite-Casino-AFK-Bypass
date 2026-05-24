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

    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    # Disabled saving the text debug image every 0.25 seconds to save your hard drive from spam!
    # cv2.imwrite("debug_text_vision.png", thresh)

    text = pytesseract.image_to_string(thresh).upper()
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

    _, thresh = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        if w > 30 and h > 30:
            cropped_keycap = thresh[y:y + h, x:x + w]

            startY, startX = int(h * 0.40), int(w * 0.25)
            endX = int(w * 0.85)
            clean_keycap = cropped_keycap[startY:h, startX:endX]

            inv_cap = cv2.bitwise_not(clean_keycap)
            inner_contours, _ = cv2.findContours(inv_cap, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            ch, cw = inv_cap.shape

            for icnt in inner_contours:
                ix, iy, iw, ih = cv2.boundingRect(icnt)

                if ix > 2 and iy > 2 and (ix + iw) < (cw - 2) and (iy + ih) < (ch - 2):
                    if iw > 5 and ih > 5:

                        letter_crop = clean_keycap[iy:iy + ih, ix:ix + iw]

                        final_img = cv2.resize(letter_crop, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
                        final_img = cv2.GaussianBlur(final_img, (5, 5), 0)
                        _, final_img = cv2.threshold(final_img, 150, 255, cv2.THRESH_BINARY)
                        final_img = cv2.copyMakeBorder(final_img, 50, 50, 50, 50, cv2.BORDER_CONSTANT,
                                                       value=[255, 255, 255])

                        cv2.imwrite("debug_cropped_key.png", final_img)

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

                if failsafe_counter >= 10:
                    print("Failsafe Triggered: Unlocking spacebar to prevent freezing.")
                    afk_lock = False
                    failsafe_counter = 0

                time.sleep(1)
        else:
            pydirectinput.press('space')

            # --- THE SMART SLEEP ---
            delay = random.uniform(3.5, 4.0)
            print(f"Spun slot. Waiting {delay:.2f} seconds...")

            wait_start_time = time.time()

            # Keep looping until the total delay time has passed
            while (time.time() - wait_start_time) < delay:
                # Quickly peek to see if the AFK check appeared during the wait
                if check_for_afk_prompt():
                    print("\n*** Prompt detected mid-spin! Interrupting wait... ***")
                    afk_lock = True
                    break  # Instantly break out of this waiting loop and solve the check

                # Sleep in tiny 0.25 second chunks instead of one massive block
                time.sleep(0.25)

except KeyboardInterrupt:
    print("\nBot stopped by user.")