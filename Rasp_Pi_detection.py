import time
import os
import joblib
import numpy as np
import pandas as pd
import subprocess

from smbus2 import SMBus
import RPi.GPIO as GPIO

import board
import busio
import adafruit_ssd1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# Attempt to load larger fonts for OLED, fallback to default if not available
try:
    # Typically available on Raspberry Pi
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
except IOError:
    try:
        font_large = ImageFont.load_default(size=20)
        font_medium = ImageFont.load_default(size=15)
        font_small = ImageFont.load_default(size=11)
    except TypeError:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

def get_text_width(draw, text, font):
    if hasattr(draw, 'textbbox'):
        return draw.textbbox((0, 0), text, font=font)[2]
    else:
        return draw.textsize(text, font=font)[0]

#load model fix
model = joblib.load("svm_rbf_fix.pkl")
print("Model loaded")

BUTTON_PIN = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(
    BUTTON_PIN,
    GPIO.IN,
    pull_up_down=GPIO.PUD_UP
)

MPU_ADDR = 0x68
PWR_MGMT_1 = 0x6B

bus = SMBus(1)
bus.write_byte_data(MPU_ADDR, PWR_MGMT_1, 0)

WIDTH = 128
HEIGHT = 64

i2c = busio.I2C(board.SCL, board.SDA)

oled = adafruit_ssd1306.SSD1306_I2C(
    WIDTH,
    HEIGHT,
    i2c,
    addr=0x3C
)

def show_oled(line1="", line2="", line3=""):
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    draw.text((0, 0), line1, fill=255)
    draw.text((0, 20), line2, fill=255)
    draw.text((0, 40), line3, fill=255)

    oled.fill(0)
    oled.image(image)
    oled.show()

#bar
def show_recording_progress(current, total):
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    # Center "Recording" text
    text = "Recording"
    text_width = get_text_width(draw, text, font_large)
    x = (WIDTH - text_width) // 2
    draw.text((x, 5), text, font=font_large, fill=255)
    
    # Draw progress bar
    fraction = current / total
    if fraction > 1.0:
        fraction = 1.0
    bar_width = int(fraction * 118)
    
    # Draw outline
    draw.rectangle((5, 40, 123, 55), outline=255, fill=0)
    # Draw filled portion
    draw.rectangle((5, 40, 5 + bar_width, 55), outline=255, fill=255)

    oled.fill(0)
    oled.image(image)
    oled.show()

#result
def show_result_oled(result_text, ratio):
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    # Center result text
    text_width = get_text_width(draw, result_text, font_large)
    x = (WIDTH - text_width) // 2
    draw.text((x, 5), result_text, font=font_large, fill=255)
    
    # Center ratio
    ratio_text = f"Ratio: {ratio:.2f}"
    text_width = get_text_width(draw, ratio_text, font_medium)
    x = (WIDTH - text_width) // 2
    draw.text((x, 30), ratio_text, font=font_medium, fill=255)
    
    # Small instructions at bottom
    menu_text = "Press to Menu"
    text_width = get_text_width(draw, menu_text, font_small)
    x = (WIDTH - text_width) // 2
    draw.text((x, 50), menu_text, font=font_small, fill=255)
    
    oled.fill(0)
    oled.image(image)
    oled.show()

#menu
def show_menu(selected):
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    draw.text((0, 0), "Tremor Detection", fill=255)

    # Menu 1
    if selected == 0:
        draw.rectangle((0, 18, 127, 36), outline=255, fill=255)
        draw.text((8, 22), "> Start Detection", fill=0)
    else:
        draw.text((8, 22), "  Start Detection", fill=255)

    # Menu 2
    if selected == 1:
        draw.rectangle((0, 42, 127, 60), outline=255, fill=255)
        draw.text((8, 46), "> Shutdown", fill=0)
    else:
        draw.text((8, 46), "  Shutdown", fill=255)

    oled.fill(0)
    oled.image(image)
    oled.show()

def show_hold_animation(title, elapsed, target):
    progress = elapsed / target

    if progress > 1:
        progress = 1

    bar_width = int(progress * 118)

    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    draw.text((0, 0), title, fill=255)
    draw.text((0, 18), f"Hold {elapsed:.1f}/{target}s", fill=255)

    # progress bar
    draw.rectangle((5, 42, 123, 55), outline=255, fill=0)
    draw.rectangle((5, 42, 5 + bar_width, 55), outline=255, fill=255)

    oled.fill(0)
    oled.image(image)
    oled.show()

def wait_release():
    while GPIO.input(BUTTON_PIN) == GPIO.LOW:
        time.sleep(0.05)

def get_button_hold():
    start = time.time()

    while GPIO.input(BUTTON_PIN) == GPIO.LOW:
        time.sleep(0.05)

    return time.time() - start

def wait_single_press():
    while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
        time.sleep(0.05)

    wait_release()
    time.sleep(0.2)

def read_word(reg):
    high = bus.read_byte_data(MPU_ADDR, reg)
    low = bus.read_byte_data(MPU_ADDR, reg + 1)

    value = (high << 8) + low

    if value >= 32768:
        value -= 65536

    return value

def read_accel():
    ax_raw = read_word(0x3B)
    ay_raw = read_word(0x3D)
    az_raw = read_word(0x3F)

    ax = ax_raw / 16384.0 * 9.80665
    ay = ay_raw / 16384.0 * 9.80665
    az = az_raw / 16384.0 * 9.80665

    return ax, ay, az

#ext feature formula
def MAV(x):
    return np.mean(np.abs(x))

def RMS(x):
    return np.sqrt(np.mean(np.square(x)))

def WL(x):
    return np.sum(np.abs(np.diff(x)))

def DASDV(x):
    diff = np.diff(x)
    return np.sqrt(np.mean(np.square(diff)))

#samain yg fix
TOTAL_SAMPLES = 1800
WINDOW_SIZE = 600
STEP = 50
THRESHOLD_RATIO = 0.5

def record_data():
    show_recording_progress(0, TOTAL_SAMPLES)

    print("Recording samples...")

    mag_buffer = []

    for i in range(TOTAL_SAMPLES):
        ax, ay, az = read_accel()

        mag = np.sqrt(
            ax * ax +
            ay * ay +
            az * az
        )

        mag_buffer.append(mag)

        if i < 10:
            print(
                f"ax={ax:.4f} ay={ay:.4f} az={az:.4f} mag={mag:.4f}"
            )

        if i % 100 == 0:
            # Update bar more frequently
            show_recording_progress(i, TOTAL_SAMPLES)

        if i % 500 == 0:
            print(f"{i}/{TOTAL_SAMPLES}")

        time.sleep(0.01)
        
    show_recording_progress(TOTAL_SAMPLES, TOTAL_SAMPLES)
    print("Recording complete")
    return mag_buffer

#ext feat
def extract_features(mag_buffer):
    show_oled("Processing...")

    features_list = []

    for start in range(
        0,
        len(mag_buffer) - WINDOW_SIZE + 1,
        STEP
    ):
        window = np.array(
            mag_buffer[start:start + WINDOW_SIZE]
        )

        features_list.append([
            MAV(window),
            RMS(window),
            WL(window),
            DASDV(window)
        ])

    features_df = pd.DataFrame(
        features_list,
        columns=[
            "MAV",
            "RMS",
            "WL",
            "DASDV"
        ]
    )

    print()
    print("===== FEATURE SAMPLE =====")
    print(features_df.head())

    print()
    print("===== FEATURE STATS =====")
    print(features_df.describe())

    return features_df

#pred
def predict_result(features_df):
    predictions = model.predict(features_df)

    print()
    print("===== WINDOW VOTING =====")

    for i, pred in enumerate(predictions):
        if pred == 1:
            label = "TREMOR"
        else:
            label = "NORMAL"

        print(
            f"Window {i+1:02d} | "
            f"MAV={features_df.iloc[i]['MAV']:.3f} | "
            f"RMS={features_df.iloc[i]['RMS']:.3f} | "
            f"WL={features_df.iloc[i]['WL']:.3f} | "
            f"DASDV={features_df.iloc[i]['DASDV']:.3f} | "
            f"{label}"
        )

    tremor_count = int(np.sum(predictions))
    normal_count = len(predictions) - tremor_count
    total_windows = len(predictions)

    ratio = tremor_count / total_windows

    print()
    print("===== VOTING SUMMARY =====")
    print("NORMAL :", normal_count)
    print("TREMOR :", tremor_count)

    print()
    print("===== RESULT =====")
    print("Total Window :", total_windows)
    print("Tremor Count :", tremor_count)
    print("Ratio :", ratio)

    if ratio > THRESHOLD_RATIO:
        result = "TREMOR"
    else:
        result = "NORMAL"

    print("HASIL :", result)

    show_result_oled(result, ratio)

    return result, ratio, tremor_count, total_windows

#detection
def run_detection():
    mag_buffer = record_data()
    features_df = extract_features(mag_buffer)
    predict_result(features_df)

    print("Press button to back menu")
    wait_single_press()

#balik ke menu
def menu_loop():
    selected = 0

    while True:
        show_menu(selected)

        while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            time.sleep(0.05)

        start_hold = time.time()

        while GPIO.input(BUTTON_PIN) == GPIO.LOW:
            elapsed = time.time() - start_hold

            if selected == 0:
                show_hold_animation(
                    "Start detection",
                    elapsed,
                    3
                )

                if elapsed >= 3:
                    wait_release()
                    print("Start detection")
                    run_detection()
                    break

            else:
                show_hold_animation(
                    "Shutdown",
                    elapsed,
                    5
                )

                if elapsed >= 5:
                    show_oled(
                        "Shutting Down",
                        "Please Wait"
                    )

                    print("Shutdown selected")
                    time.sleep(2)
                    subprocess.run(
			["/usr/sbin/shutdown", "-h", "now"]
		    )
                    return

            time.sleep(0.1)

        else:
            pass

        hold_time = time.time() - start_hold

        # kalau ditekan sebentar, pindah menu
        if hold_time < 1:
            selected = 1 - selected

        time.sleep(0.2)

#start
try:
    show_oled(
        "Tremor Detection",
        "Starting..."
    )

    time.sleep(2)

    menu_loop()

except KeyboardInterrupt:
    print("\nProgram stopped by user")

finally:
    show_oled(
        "Program",
        "Stopped"
    )

    GPIO.cleanup()
    bus.close()

    print("GPIO cleaned")
