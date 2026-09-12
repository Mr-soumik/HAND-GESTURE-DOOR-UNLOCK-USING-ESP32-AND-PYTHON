import cv2
import mediapipe as mp
import serial
import time
import math

# by TechTadka360, please like,share and subscribe our social media channels.

ESP32_PORT = 'COM7'  # Please enter your correct COM port
BAUD_RATE = 115200

# unlock patern seequence
# 0  1  2
# 3  4  5
# 6  7  8
CORRECT_PATTERN = [0, 1, 2, 5, 8]

try:
    esp = serial.Serial(ESP32_PORT, BAUD_RATE, timeout=1)
    esp.dtr = False
    esp.rts = False
    time.sleep(2)
    esp.reset_input_buffer()
    esp.reset_output_buffer()
    print("ESP32 Connected Successfully!")
except Exception as e:
    print(f"Serial Error: {e}")
    esp = None

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
cap = cv2.VideoCapture(0)

grid_points = []
current_pattern = []
is_unlocked = False
cooldown_timer = 0


popup_message = ""
popup_color = (0, 0, 0)
popup_timer = 0

def get_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

   
    if not grid_points:
        start_x, start_y = w // 2 - 120, h // 2 - 100
        step = 120
        for r in range(3):
            for c in range(3):
                grid_points.append((start_x + c * step, start_y + r * step))

    
    for idx, pt in enumerate(grid_points):
        pt_col = (0, 255, 255) if idx in current_pattern else (200, 200, 200)
        cv2.circle(frame, pt, 18, pt_col, -1)
        cv2.putText(frame, str(idx), (pt[0] - 6, pt[1] + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    
    for i in range(len(current_pattern) - 1):
        p1 = grid_points[current_pattern[i]]
        p2 = grid_points[current_pattern[i + 1]]
        cv2.line(frame, p1, p2, (0, 255, 0), 4)

    
    cv2.rectangle(frame, (30, 20), (160, 70), (0, 200, 0), -1)
    cv2.putText(frame, "SUBMIT", (45, 53), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

   
    cv2.rectangle(frame, (w - 160, 20), (w - 30, 70), (0, 140, 255), -1)
    cv2.putText(frame, "RESET", (w - 145, 53), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    
    btn_col = (0, 0, 255) if is_unlocked else (80, 80, 80)
    cv2.rectangle(frame, (w // 2 - 130, h - 75), (w // 2 + 130, h - 20), btn_col, -1)
    cv2.putText(frame, "TOUCH TO LOCK", (w // 2 - 105, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm = hand_landmarks.landmark
            index_tip = (int(lm[8].x * w), int(lm[8].y * h))

            cv2.circle(frame, index_tip, 8, (255, 0, 0), -1)

           
            if not is_unlocked:
                for idx, pt in enumerate(grid_points):
                    if get_distance(index_tip, pt) < 30:
                        if idx not in current_pattern:
                            current_pattern.append(idx)

            current_time = time.time()
            if current_time - cooldown_timer > 1.2:
                
                if 30 <= index_tip[0] <= 160 and 20 <= index_tip[1] <= 70:
                    if current_pattern == CORRECT_PATTERN:
                        if esp:
                            esp.write(b'U\n')
                            esp.flush()
                        is_unlocked = True
                        popup_message = "SUCCESSFULLY UNLOCKED!"
                        popup_color = (0, 200, 0)
                        popup_timer = time.time()
                    else:
                        if esp:
                            esp.write(b'W\n')
                            esp.flush()
                        popup_message = "YOUR PASSWORD IS WRONG!"
                        popup_color = (0, 0, 255)
                        popup_timer = time.time()
                    current_pattern = []
                    cooldown_timer = current_time

                # RESET 
                elif (w - 160) <= index_tip[0] <= (w - 30) and 20 <= index_tip[1] <= 70:
                    current_pattern = []
                    popup_message = "PATTERN CLEARED"
                    popup_color = (0, 140, 255)
                    popup_timer = time.time()
                    cooldown_timer = current_time

                # TOUCH TO LOCK 
                elif (w // 2 - 130) <= index_tip[0] <= (w // 2 + 130) and (h - 75) <= index_tip[1] <= (h - 20):
                    if is_unlocked:
                        if esp:
                            esp.write(b'L\n')
                            esp.flush()
                        is_unlocked = False
                        current_pattern = []
                        popup_message = "DOOR LOCKED!"
                        popup_color = (0, 0, 255)
                        popup_timer = time.time()
                        cooldown_timer = current_time

   
    status_str = "STATUS: UNLOCKED" if is_unlocked else "STATUS: LOCKED"
    status_col = (0, 255, 0) if is_unlocked else (0, 0, 255)
    cv2.putText(frame, status_str, (w // 2 - 110, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.75, status_col, 2)

   
    if time.time() - popup_timer < 3.0 and popup_message:
        banner_y1, banner_y2 = h // 2 - 35, h // 2 + 35
        cv2.rectangle(frame, (40, banner_y1), (w - 40, banner_y2), (20, 20, 20), -1)
        cv2.rectangle(frame, (40, banner_y1), (w - 40, banner_y2), popup_color, 3)
        
        text_size = cv2.getTextSize(popup_message, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
        text_x = (w - text_size[0]) // 2
        cv2.putText(frame, popup_message, (text_x, h // 2 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, popup_color, 2)

    cv2.imshow("Smart Gesture Security Door", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if esp:
    esp.write(b'L\n')
    esp.flush()
    esp.close()
cap.release()
cv2.destroyAllWindows()