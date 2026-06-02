# Tower Unite Automata: Advanced OCR & Vision Pipeline

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-green.svg)
![Tesseract](https://img.shields.io/badge/Tesseract-OCR-red.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

An advanced, asynchronous computer vision script designed to autonomously operate Tower Unite slot machines while mathematically identifying, isolating, and solving the game's dynamic anti-AFK checks in real-time. 

Unlike basic pixel-search macros, this project utilizes a multi-layered image processing pipeline to defeat dynamic backgrounds, translucent UI elements, 3D object occlusion, and isometric shadows.

### ⚠️ Legal & Ethical Disclaimer
**This project was created strictly as a proof-of-concept and educational exercise in Computer Vision, Image Processing, and Optical Character Recognition (OCR).** Using automation scripts or macros violates the Tower Unite Terms of Service (TOS). Using this software on official servers will likely result in a permanent account ban. The author assumes **zero liability** for any bans, damages, or account losses incurred by using this code. **Use entirely at your own risk.**

---

## 🔬 Core Features & Tech Stack

This isn't your standard `pyautogui.locateOnScreen()` script. The game throws dynamic 3D objects, spinning backgrounds, and complex lighting at the player. To beat this, the script runs a custom OpenCV/Tesseract pipeline:

* **Smart Sleep State Machine:** Instead of using blocking `time.sleep()` calls that blind the bot during slot spins, the script utilizes a rapid-polling asynchronous sleep loop. It checks the screen for prompts every 0.25 seconds while maintaining human-like randomized macro delays (2.5s - 3.0s).
* **Algorithmic 4-Way Guillotine Crop:** Automatically calculates bounding boxes around isolated shapes and mathematically slices off the top 38% and left 25% of the object to instantly delete 3D hardhat occlusion and isometric drop-shadows.
* **Center-Gravity Matrix:** An advanced noise-rejection filter. If the bounding box accidentally catches corner debris (shadows or UI fragments) during a fast animation frame, the center-gravity filter calculates the distance of the debris from the absolute center and rejects it instantly.
* **Shape Profile & Complexity Thresholding:** To prevent the OCR from trying to read giant casino banners or complex background walls, the pipeline calculates the Aspect Ratio, Pixel Density, and Internal Contour Count of every shape. Complex background geometry is instantly thrown out.
* **Heavy Anti-Aliasing & Upscaling Pipeline:** Tesseract OCR is designed for high-resolution book fonts, not pixelated game textures. This script upscales captured shapes by **500% (Cubic Interpolation)**, applies a heavy **(15, 15) Gaussian Blur** to melt 8-bit jagged edges, and snaps them back to crisp vector-style lines using binary re-thresholding before feeding them to the OCR engine (utilizing PSM 8 for robust character recognition).

---

## ⚙️ Prerequisites & Installation

1. **Install Python 3.8+**
2. **Install Tesseract-OCR:**
   * Download and install Tesseract for Windows: [UB-Mannheim Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
   * Note your installation path (Default is usually `C:\Program Files\Tesseract-OCR\tesseract.exe`).
3. **Install required Python libraries:**
   ```bash
   pip install opencv-python pytesseract pyautogui pydirectinput numpy
   ```

---

## 📐 Resolution Configuration (READ CAREFULLY)

**Out of the box, this script is hardcoded specifically for a `1920x1080` monitor resolution with 100% Windows UI Scaling.**

Because the script maps specific screen coordinates to avoid processing the entire 1080p frame (which would destroy CPU performance), it only looks at specific "zones". 

### How to adapt this for 1440p, 4K, or Ultrawide:
If you are running a different resolution, you must re-measure the coordinate zones.

1. Open Tower Unite and trigger the AFK check.
2. Take a full-screen screenshot.
3. Open the screenshot in an image editor (like MS Paint or Photoshop).
4. Hover your mouse to find the `(X, Y)` coordinates of the top-left corner of the zones, and measure the `Width` and `Height` of the boxes.
5. Update the `CONFIGURATION` section at the top of `main.py`:

```python
# The format is (Top-Left X, Top-Left Y, Width, Height)
AFK_TEXT_REGION = (700, 320, 520, 100)  # The zone where the "ARE YOU STILL THERE?" text appears
AFK_KEY_AREA = (649, 420, 537, 144)     # The zone where the bouncing keycap travels
ERROR_TEXT_REGION = (800, 440, 320, 80) # The zone where the red "Wrong Button" text appears
```

*Tip: The script saves debug images (`debug_raw_keycap_area.png` and `debug_cropped_key.png`) to your folder every time it runs. Check these images to ensure your coordinates are perfectly framing the keycap!*

---

## 💻 Usage Instructions

1. Open Tower Unite and sit at a slot machine.
2. Open your terminal and run the script:
   ```bash
   python main.py
   ```
3. You have 5 seconds to tab back into the game.
4. The bot will begin spinning. If it detects the AFK prompt, it will lock the spacebar, isolate the letter, input the correct key, and seamlessly resume spinning.
5. **To stop the bot:** Click into your terminal window and press `CTRL + C`.

---

## 📌 Known Limitations (Overnight Usage)

This script is highly resilient and generally considered **stable for overnight use**. However, please be aware of the following game-side event:

* **Server Resets:** Very rarely, the Tower Unite servers will undergo a reset or cycle. If this happens while the script is running unattended, your character will be disconnected from the casino and loaded into the default Plaza spawn point in a new server. 
* Because the script operates at the OS level, it will not recognize that the game environment has changed. It will continue running its standard loop (pressing spacebar and scanning for the AFK prompt), which will simply result in your character jumping in place at the spawn point until you manually stop the script. This is entirely harmless, but it is an unavoidable game-side limitation.

---

## 🛠️ Debugging

If the bot makes a mistake, check the root folder for the following output files generated in real-time:
* `debug_raw_keycap_area.png` - The raw, full-color capture of your coordinate zone (useful for checking lighting/UI shifts).
* `debug_text_vision.png` - The thresholded image of the text prompt.
* `debug_cropped_key.png` - The final, upscaled, blurred, and thresholded character that is fed directly to the Tesseract engine.