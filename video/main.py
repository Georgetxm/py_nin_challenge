import easygopigo3 as EasyGoPiGo3
import time
import pyttsx3
import io

# Packages for object detection
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
from object_detection import detect

# Load the classifier files
stop_cascade = cv2.CascadeClassifier("cascade_xml/stop_sign.xml")
light_cascade = cv2.CascadeClassifier("cascade_xml/traffic_light.xml")
person_cascade = cv2.CascadeClassifier("cascade_xml/pedestrian.xml")

# Instantiate GoPiGo, servo, sensor and text to speech
gpg = EasyGoPiGo3.EasyGoPiGo3()
dist_sensor = gpg.init_distance_sensor()
servo1 = gpg.init_servo("SERVO1")
engine = pyttsx3.init()

# Instantiate Camera Object
camera = PiCamera()

# Set Camera's resolution
camera.resolution = (640, 480)

# Cap framerate to be slightly above 30
camera.framerate = 32

# Create object that gives access to PiCamera's stream
# while providing performance boost with OpenCV library
rawCapture = PiRGBArray(camera, size=(640, 480))

# Allow the camera to warmup
time.sleep(0.1)

# Minimum distance from GoPiGo
min_dist = 5

# List of servo degrees to turn
servo_deg_list = [0, 20, 40, 60, 80, 100, 120, 140, 160, 180]

# List to store read distances
dist_list = []

try:
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        current_dist = 20
        frame = frame.array

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Object detection
        stop_detected = detect(stop_cascade, gray, frame)
        light_detected = detect(light_cascade, gray, frame)
        person_detected = detect(person_cascade, gray, frame)

        # Show frame with drawn bounding boxes
        cv2.imshow('image', frame)

        if current_dist < min_dist:
            gpg.stop()
            engine.say("Obstacle detected, re-routing")
            engine.runAndWait()

            # Turns servo to check for all distance
            for deg in servo_deg_list:
                servo1.rotate_servo(deg)
                dist_list.append(dist_sensor.read())

            # Get index of max distance found by dist sensor
            max_idx = dist_list.index(max(dist_list))

            # Turn towards where max dist was found
            # Servo's right is 0 deg and left is 180 deg
            # While GPG body's right is 90 deg and left is -90 deg
            # To match the difference and turn GPG, 90 is subtracted by the servo's degree
            gpg.turn_degrees(90 - servo_deg_list[max_idx])

        # Stops GPG when detected a person and near it
        elif person_detected and current_dist < min_dist:
            gpg.stop()
            engine.say("Person detected, re-routing")
            engine.runAndWait()
            gpg.orbit(30, 30)
            gpg.orbit(-30, 30)

        # Stops GPG when detected a stop sign and near it
        elif stop_detected and current_dist < min_dist:
            gpg.stop()
            engine.say("Destination reached.")
            engine.runAndWait()
            break

        # Detected a traffic light; advance when green
        elif light_detected:
            engine.say("Traffic light detected.")
            engine.runAndWait()
            if light_detected == "RED":
                gpg.stop()
                engine.say("Red light is on, stopping.")
                engine.runAndWait()
            elif light_detected == "GREEN":
                engine.say("Green light is on, advancing.")
                engine.runAndWait()
                gpg.forward()

        # If there are no obstructions and nothing is detected
        else:
            gpg.forward()

        # cv2.imshow('img', frame)
        key = cv2.waitKey(1) & 0xFF

        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)

        # Press 'q' to quit
        if key == ord('q'):
            break

finally:
    camera.close()
