import time
import random
import pydirectinput
import pyautogui
import pytesseract
import cv2
import numpy as np

# --- CONFIGURATION ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Updated Coordinates based on your new images
# Shifted Y down by 15 pixels so the bottom of the letters aren't cut off
AFK_TEXT_REGION = (750, 365, 420, 40)

# This is now a wide box covering the entire red rectangle area you drew
AFK_KEY_AREA = (720, 400, 480, 110)

# The error message box coordinates
ERROR_TEXT_REGION = (800, 440, 320, 80)


def check_for_afk_prompt():
    screenshot = pyautogui.screenshot(region=AFK_TEXT_REGION)
    gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    cv2.imwrite("debug_text_vision.png", gray)  # Keep saving for debugging

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

    # NEW THRESHOLD MATH:
    # This turns the grey keycap white, and keeps the black letter (and dark background) black.
    # Tesseract loves reading black text on a white background.
    _, thresh = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY)

    cv2.imwrite("debug_keycap_vision.png", thresh)  # Check this file!

    # --psm 11 tells Tesseract to look for scattered text anywhere in the wide image
    config = '--psm 11'
    raw_text = pytesseract.image_to_string(thresh, config=config).strip().lower()

    # Because we are scanning a wider area, we might pick up random noise.
    # We must filter the result to find exactly ONE letter.
    # We loop through whatever Tesseract found and return the first valid alphabet letter.
    for char in raw_text:
        if char.isalpha() and char.islower():
            return char

    return None


# --- MAIN LOOP ---
print("Starting in 5 seconds. Please tab into Tower Unite...")
time.sleep(5)
print("Bot running. Press CTRL+C to stop.")

try:
    while True:
        if check_for_afk_prompt():
            print("\n*** AFK Check Detected! ***")

            # Give the moving keycap a split second to settle
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
                print("Could not find a valid letter in the red box area. Retrying...")
                time.sleep(1)
        else:
            pydirectinput.press('space')
            delay = random.uniform(2.0, 3.0)
            print(f"Spun slot. Waiting {delay:.2f} seconds...")
            time.sleep(delay)

except KeyboardInterrupt:
    print("\nBot stopped by user.")