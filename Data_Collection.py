import serial
import time

# Configuration
SERIAL_PORT = "COM9"
BAUD_RATE = 115200
DURATION = 60  # Seconds
FILENAME = "vitotespredict1.csv"

# Initialize Serial
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset/initialize
    ser.reset_input_buffer() # Clear old data from the buffer
    print(f"Connected to {SERIAL_PORT}. Starting recording for {DURATION}s...")
except Exception as e:
    print(f"Error: {e}")
    exit()

with open(FILENAME, "w") as f:
    # 1. Manually write the header to ensure it's always at the top
    f.write("time_ms,ax,ay,az,gx,gy,gz\n")
    
    start_time = time.time()
    count = 0

    while time.time() - start_time < DURATION:
        try:
            # Read a line and decode
            line = ser.readline().decode('utf-8', errors='ignore').strip()

            # 2. Basic Validation: Only save if the line has 7 columns (Time + 6 Axis)
            # This prevents "Initializing..." or "MPU READY" from messing up your CSV
            if line and line.count(',') == 6:
                f.write(line + "\n")
                count += 1
                
                # Print every 100 lines so the console isn't overwhelmed
                if count % 100 == 0:
                    print(f"Recorded {count} samples...")
        
        except KeyboardInterrupt:
            print("\nRecording stopped early by user.")
            break

ser.close()

# 3. Verify the result
print("-" * 30)
print(f"Success! Data saved to: {FILENAME}")
print(f"Total samples captured: {count}")
if count < 5500:
    print("Warning: Sample count is low. Check your I2C/OLED speed.")
else:
    print("Sample rate looks healthy (~100Hz).")