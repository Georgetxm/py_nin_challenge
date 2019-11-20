import cv2


def detect(cascade_classifier, gray_image, image):

    # y camera coordinate of the target point 'P'
    # v = 0

    # minimum value to proceed traffic light state validation
    threshold = 150

    # detection
    cascade_obj = cascade_classifier.detectMultiScale(
        gray_image,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(14, 14))

    # draw a rectangle around the objects
    for (x_pos, y_pos, width, height) in cascade_obj:
        cv2.rectangle(image, (x_pos + 5, y_pos + 5), (x_pos +
                                                      width - 5, y_pos + height - 5), (255, 255, 255), 2)

        # As stop sign are usually squared, w/h == 1
        if width / height == 1:
            detected = "STOP"
            cv2.putText(image, detected, (x_pos, y_pos - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return detected

        # As humans are usually rectangle, taller in height, w/h == 0.5
        elif width/height == 0.5:
            detected = "Person"
            cv2.putText(image, detected, (x_pos, y_pos - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return detected

        # Traffic lights
        else:
            roi = gray_image[y_pos + 10:y_pos + height -
                             10, x_pos + 10:x_pos + width - 10]
            mask = cv2.GaussianBlur(roi, (25, 25), 0)
            (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(mask)

            # check if light is on
            if maxVal - minVal > threshold:
                cv2.circle(roi, maxLoc, 5, (255, 0, 0), 2)

                # Red light
                if 1.0 / 8 * (height - 30) < maxLoc[1] < 4.0 / 8 * (height - 30):
                    detected = "RED"
                    cv2.putText(image, detected, (x_pos + 5, y_pos - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    self.red_light = True
                    return detected

                # Green light
                elif 5.5 / 8 * (height - 30) < maxLoc[1] < height - 30:
                    detected = "GREEN"
                    cv2.putText(image, detected, (x_pos + 5, y_pos - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    self.green_light = True
                    return detected
