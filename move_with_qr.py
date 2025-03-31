from vilib import Vilib
from time import sleep
import threading
from picrawler import Picrawler

# Initialize PiCrawler
crawler = Picrawler()
speed = 80

# QR Code to Leg Mapping
qr_to_leg = {}         # Maps QR text -> leg index
qr_last_positions = {} # Stores last detected positions
next_leg = 0           # Tracks which leg to assign next
leg_positions = [
    [60, 0, -30],  # Leg 1 (Right Front)
    [60, 0, -30], # Leg 2 (Left Front)
    [60, 0, -30], # Leg 3 (Left Rear)
    [60, 0, -30]   # Leg 4 (Right Rear)
]
# Replace these values with your calibrated leg positions
DEFAULT_LEG_POSITIONS = [
    [60, 0, -30],  # Leg 1 (Right Front)
    [60, 0, -30], # Leg 2 (Left Front)
    [60, 0, -30], # Leg 3 (Left Rear)
    [60, 0, -30]   # Leg 4 (Right Rear)
]

def set_default_leg_positions():
    """Move all legs to the calibrated default position."""
    for leg, pos in enumerate(DEFAULT_LEG_POSITIONS):
        crawler.do_single_leg(leg, pos, speed)
    print("🦿 PiCrawler moved to CALIBRATED default position.")

def get_qr_data():
    """Retrieve QR code text and position from Vilib."""
    qr_text = Vilib.detect_obj_parameter.get('qr_data', "None")
    if qr_text == "None":
        return None, None
    pos = (
        Vilib.detect_obj_parameter.get('qr_x', 0),
        Vilib.detect_obj_parameter.get('qr_y', 0),
        Vilib.detect_obj_parameter.get('qr_z', 0)
    )
    return qr_text, pos

def qr_detection_thread():
    """Continuously detects QR codes, maps them to legs, and moves legs."""
    global next_leg
    while True:
        qr_text, pos = get_qr_data()
        if qr_text is not None and pos is not None:
            # Assign new QR codes to a leg if not already mapped
            if qr_text not in qr_to_leg and next_leg < 4:
                qr_to_leg[qr_text] = next_leg
                qr_last_positions[qr_text] = pos
                print(f"✅ QR Code '{qr_text}' → Assigned to Leg {next_leg + 1}")
                next_leg += 1
            elif qr_text in qr_to_leg:
                # Compute movement delta
                last_pos = qr_last_positions.get(qr_text, pos)
                delta = tuple(pos[i] - last_pos[i] for i in range(3))

                # Move leg if significant movement detected
                if any(abs(d) > 1 for d in delta):
                    leg = qr_to_leg[qr_text]
                    leg_positions[leg] = [
                        leg_positions[leg][i] + delta[i] for i in range(3)
                    ]
                    print(f"➡️ Moving Leg {leg + 1} (QR: '{qr_text}') Δ {delta}")
                    crawler.do_single_leg(leg, leg_positions[leg], speed)
                    qr_last_positions[qr_text] = pos

        sleep(0.2)

def main():
    """Main function to start camera display and QR detection."""
    # Start the camera and enable local display
    Vilib.camera_start(vflip=False, hflip=False)
    Vilib.display(local=True, web=True)
    Vilib.qrcode_detect_switch(True)  # Automatically start QR detection
    sleep(1)  # Allow time for camera to start

    # Set PiCrawler to default 0 position
    crawler.do_step('stand', speed)  # Change to 'sit' if needed
    print("🦿 PiCrawler set to default position.")

    # Start the QR detection thread
    thread = threading.Thread(target=qr_detection_thread, daemon=True)
    thread.start()

    # Keep the main thread running
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        Vilib.qrcode_detect_switch(False)
        Vilib.camera_close()
        print("\nExiting...")

if __name__ == "__main__":
    main()
