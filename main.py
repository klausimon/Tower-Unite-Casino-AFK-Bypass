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
    """Looks for the main AFK check text in the upper box."""
    screenshot = pyautogui.screenshot(region=AFK_TEXT_REGION)
    gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    # Saves what the bot sees for the text (Useful if UI scales change)
    cv2.imwrite("debug_text_vision.png", gray)

    text = pytesseract.image_to_string(gray).upper()
    return "STILL" in text or "THERE" in text


def check_for_error():
    """Looks for the red penalty text after a misclick."""
    screenshot = pyautogui.screenshot(region=ERROR_TEXT_REGION)
    gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    text = pytesseract.image_to_string(gray).upper()
    return "WRONG" in text or "BUTTON" in text


def get_afk_key():
    """Finds the white keycap, slices off the hardhat, and reads the letter."""
    screenshot = pyautogui.screenshot(region=AFK_KEY_AREA)
    img = np.array(screenshot)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Turn the grey keycap pure white, and the background pure black
    _, thresh = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY)
    cv2.imwrite("debug_keycap_full_area.png", thresh)

    # Find all isolated white shapes in the black void
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        # We only care about shapes larger than 30x30 pixels (ignores the mouse cursor)
        if w > 30 and h > 30:
            # Crop the image strictly to the keycap box!
            cropped_keycap = thresh[y:y + h, x:x + w]

            # --- THE GUILLOTINE ---
            # Calculate what 40% of the image height is
            chop_amount = int(h * 0.40)

            # Slice off the top 40% to remove the hardhat pieces
            clean_keycap = cropped_keycap[chop_amount:h, 0:w]

            # Save the clean cropped image so you can see exactly what Tesseract reads
            cv2.imwrite("debug_cropped_key.png", clean_keycap)

            # config explains:
            # --psm 10 : Expect exactly ONE character.
            # whitelist: Only allow lowercase alphabet letters (ignores noise/symbols).
            config = '--psm 10 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz'
            char = pytesseract.image_to_string(clean_keycap, config=config).strip().lower()

            # Final validation check: Ensure it is a single valid alphabet letter
            if len(char) == 1 and char.isalpha():
                return char

    return None


# --- MAIN LOOP ---
print("Starting in 5 seconds. Please tab into Tower Unite...")
time.sleep(5)
print("Bot running. Press CTRL+C in this console to stop.")

try:
    while True:
        # 1. Check if the AFK box is on screen
        if check_for_afk_prompt():
            print("\n*** AFK Check Detected! ***")

            # Give the keycap a tiny fraction of a second to stop bouncing/spawning
            time.sleep(0.5)

            # 2. Extract the letter
            key_to_press = get_afk_key()

            if key_to_press:
                print(f"Pressing key: {key_to_press}")
                pydirectinput.press(key_to_press)
                time.sleep(1)  # Let the game process the input

                # 3. Verify if we hit the right key or got the penalty
                if check_for_error():
                    print("Misclick detected! Waiting 3.5 seconds penalty...")
                    time.sleep(3.5)  # Wait out the penalty + buffer
                else:
                    print("Success! Resuming...")
                    time.sleep(1)
            else:
                print("Could not isolate a valid letter. Retrying next loop...")
                time.sleep(1)
        else:
            # 4. Normal slot machine operation
            pydirectinput.press('space')

            # Randomized delay to look human to the server
            delay = random.uniform(2.0, 3.0)
            print(f"Spun slot. Waiting {delay:.2f} seconds...")
            time.sleep(delay)

except KeyboardInterrupt:
    print("\nBot stopped by user.")