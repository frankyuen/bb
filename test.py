import cv2

# Initialize video capture
cap = cv2.VideoCapture(0)

# Initialize background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2()

detect_count = 0

# Loop through frames
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    
    # Apply background subtraction
    fgmask = fgbg.apply(frame)
    
    # Apply thresholding to remove noise
    th = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)[1]
    # th = cv2.adaptiveThreshold(fgmask, 200, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Find contours of objects
    contours, hierarchy = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Loop through detected objects
    for contour in contours:
        # Calculate area of object
        area = cv2.contourArea(contour)
        
        # Filter out small objects
        if area > 100:
            # Get bounding box coordinates
            x, y, w, h = cv2.boundingRect(contour)
            
            # Draw bounding box around object
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            detect_count += 1
            print('object detected: {}'.format(detect_count))

    
    # Display the resulting frame
    cv2.imshow('Motion detection', frame)
    # cv2.imshow('Motion detection', cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE))
    # cv2.imshow('Motion detection', cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE))

    
    # Exit loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video capture and destroy windows
cap.release()
cv2.destroyAllWindows()

