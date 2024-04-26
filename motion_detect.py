import sys
import cv2
import logging
import smtplib
from email.message import EmailMessage
from os import getenv

from datetime import datetime, timedelta, timezone
from time import sleep
from dotenv import load_dotenv

load_dotenv()

EMAIL_SERVER = getenv('EMAIL_SERVER')
SENDER = getenv('SENDER')
RECIPENT = getenv('RECIPENT')

ALERT_INTERVAL_SECS = 1800 if getenv('ALERT_INTERVAL_SECS') is None else int(getenv('ALERT_INTERVAL_SECS'))

SHOW_UI = getenv('SHOW_UI') == 'True'

LOOP_PER_SCAN = 400 if getenv('LOOP_PER_SCAN') is None else int(getenv('LOOP_PER_SCAN'))
IGNORE_INITIAL_LOOPS = 20 if getenv('IGNORE_INITIAL_LOOPS') is None else int(getenv('IGNORE_INITIAL_LOOPS'))

ROTATE = 0 if getenv('ROTATE') is None else int(getenv('ROTATE'))
COUNT_THRESHOLD = 0.05 if getenv('COUNT_THRESHOLD') is None else float(getenv('COUNT_THRESHOLD'))

LAST_ALERT_PATH = getenv('LAST_ALERT_PATH')
IMAGE_FOLDER = getenv('IMAGE_FOLDER')

SAVE_ANYWAY = getenv('SAVE_ANYWAY') == 'True'

cv_rotate = None
if ROTATE == 90:
    cv_rotate = cv2.ROTATE_90_CLOCKWISE
elif ROTATE == 180:
    cv_rotate = cv2.ROTATE_180
elif ROTATE == 270:
    cv_rotate = cv2.ROTATE_90_COUNTERCLOCKWISE

def motion_detect():
    # Initialize video capture
    cap = cv2.VideoCapture(0)

    # Initialize background subtractor
    fgbg = cv2.createBackgroundSubtractorMOG2()

    raw_count = 0
    written = False

    # Loop through frames
    for i in range(LOOP_PER_SCAN):
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

                    if IMAGE_FOLDER and not written:
                        cv2.imwrite('{}/bb-{}.jpg'.format(IMAGE_FOLDER, datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')), frame)
                        written = True

        if SAVE_ANYWAY and IMAGE_FOLDER and not written:
            cv2.imwrite('{}/bb-{}.jpg'.format(IMAGE_FOLDER, datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')), frame)
            written = True

        # Display the resulting frame
        if SHOW_UI:
            cv2.imshow('Motion detection', frame)
            cv2.waitKey(1)

    # Release video capture and destroy windows
    cap.release()
    cv2.destroyAllWindows()

    return (raw_count, datetime.now(timezone.utc))

def send_alert(raw_count):
    if not EMAIL_SERVER or not SENDER or not RECIPENT:
        logging.info('Alert service not configured. No alert sent. This message is informational only, not an error')
        return

    try:
        send_email()
        logging.info('Alert sent')
    except Exception as e:
        logging.warning('Failed to send the email alert')
        logging.warning(e)

    if not LAST_ALERT_PATH:
        return

    try:
        with open(LAST_ALERT_PATH, 'w') as f:
            f.writelines(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z'))
    except Exception as e:
        logging.warning('Failed to write last alert')
        logging.warning(e)



def send_email():
    msg = EmailMessage()
    msg.set_content('As captioned')
    msg['Subject'] = '[Castle]:  Motion detected'
    msg['From'] = SENDER
    msg['To'] = RECIPENT

    s = smtplib.SMTP(EMAIL_SERVER)
    s.send_message(msg)
    s.quit()


def config_logger():
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] - %(message)s',
                        level=logging.INFO)

def main():
    config_logger()
    logging.info('Started')

    detection_threshold = (LOOP_PER_SCAN - IGNORE_INITIAL_LOOPS) * COUNT_THRESHOLD

    first_line = None
    	
    try:
        with open(LAST_ALERT_PATH, 'r') as f:
            first_line = f.readline().strip('\n')
    except FileNotFoundError:
        pass

    last_alert = None
    if first_line is None:
        logging.info('No previous alert found')
    else:
        logging.info('Last alert saved: {}'.format(first_line))
        last_alert = datetime.strptime(first_line, '%Y-%m-%d %H:%M:%S%z')

    (raw_count, detection_time) = motion_detect()
    if raw_count > 0:
        if raw_count > detection_threshold:
            logging.warning('Motion detected. Raw count: {} (EXCEED threshold of {})'.format(raw_count, detection_threshold))

            if last_alert is None or last_alert + timedelta(seconds=ALERT_INTERVAL_SECS) < datetime.now(timezone.utc):
                send_alert(raw_count)
                last_alert = datetime.now(timezone.utc)
            else:
                logging.info('Skipped sending alerts. Alert interval is {} second(s)'.format(ALERT_INTERVAL_SECS))
        else:
            logging.warning('Motion detected. Raw count: {} (within threshold of {})'.format(raw_count, detection_threshold))
    else:
        logging.info('No motion detected')

    exit(0)

if __name__ == '__main__':
    main()

