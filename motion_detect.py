import sys
import cv2

from datetime import datetime, timedelta, timezone
from time import sleep

SCAN_INTERVAL_SECS = 10
ALERT_INTERVAL_SECS = 11

SHOW_UI = True

LOOP_PER_SCAN = 100
IGNORE_INITIAL_LOOPS = 40

ROTATE = 270
COUNT_THRESHOLD = 0.5

IMAGE_FOLDER = 'var'

cv_rotate = None
if ROTATE == 90:
    cv_rotate = cv2.ROTATE_90_CLOCKWISE
elif ROTATE == 180:
    cv_rotate = cv2.ROTATE_180
elif ROTATE == 270:
    cv_rotate = cv2.ROTATE_90_COUNTERCLOCKWISE

detection_threshold = (LOOP_PER_SCAN - IGNORE_INITIAL_LOOPS) * COUNT_THRESHOLD

def motion_detect():
    # Initialize video capture
    cap = cv2.VideoCapture(0)

    # Initialize background subtractor
    fgbg = cv2.createBackgroundSubtractorMOG2()

    raw_count = 0
    frame = None

    # Loop through frames
    for i in range(LOOP_PER_SCAN):
        print('Loop {} of {}'.format(i, LOOP_PER_SCAN))

        # Capture frame-by-frame
        ret, frame = cap.read()

        if cv_rotate is not None:
            frame = cv2.rotate(frame, cv_rotate)
        
        # Apply background subtraction
        fgmask = fgbg.apply(frame)
        
        # Apply thresholding to remove noise
        th = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)[1]
        
        # Find contours of objects
        contours, hierarchy = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # check after initial frames stabilized
        if i > IGNORE_INITIAL_LOOPS:
            # Loop through detected objects
            for contour in contours:
                # Calculate area of object
                area = cv2.contourArea(contour)
                
                # Filter out small objects
                if area > 100:
                    raw_count += 1

                    # Get bounding box coordinates
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Draw bounding box around object
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Display the resulting frame
        if SHOW_UI:
            cv2.imshow('Motion detection', frame)
            cv2.waitKey(1)

    cur_time = datetime.now(timezone.utc)

    if raw_count > 0:
        cv2.imwrite('{}/bb-{}.jpg'.format(IMAGE_FOLDER, cur_time.strftime('%Y-%m-%d_%H:%M:%S')), frame)

    # Release video capture and destroy windows
    cap.release()
    cv2.destroyAllWindows()

    return (raw_count, cur_time)

def send_alert(raw_count):
    # TODO: send email
    print('Detected motions at {}. Raw count is {}'.format(datetime.now(timezone.utc), raw_count))

# main script starts

last_alert = None

while True:
    (raw_count, detection_time) = motion_detect()
    if raw_count > detection_threshold and (last_alert is None or 
                                            last_alert + timedelta(seconds=ALERT_INTERVAL_SECS) < datetime.now(timezone.utc)):
        send_alert(raw_count)
        last_alert = datetime.now(timezone.utc)

    sleep(SCAN_INTERVAL_SECS)

sys.exit()
