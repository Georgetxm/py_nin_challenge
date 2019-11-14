# Import packages
import os
import cv2
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera
import tensorflow as tf
import argparse
import sys

# Import utilites
from utils import label_map_util
from utils import visualization_utils as vis_util

# Gpg packages
import easygopigo3 as EasyGoPiGo3
import time
import pyttsx3

# Set up camera constants; smaller resolution for slighty better framerates
IM_WIDTH = 640
IM_HEIGHT = 480 

# Initialising GPG, sensors, and text to speech
gpg = EasyGoPiGo3.EasyGoPiGo3()
dist_sensor = gpg.init_distance_sensor()
speaker = pyttsx3.init()

# Global variables 
camera = None
rawCapture = None

## Initialising object detection model and dependencies
# Get relative working directory; object_detection folder
sys.path.append('..')

# Name of the directory containing the object detection module we're using
MODEL_NAME = 'ssdlite_mobilenet_v2_coco_2018_05_09'

CWD_PATH = os.getcwd()

# Path to frozen detection graph .pb file, which contains the model that is used for object detection.
PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,'frozen_inference_graph.pb')

# Path to label map file
PATH_TO_LABELS = os.path.join(CWD_PATH,'data','mscoco_label_map.pbtxt')

# Number of classes the object detector can identify
NUM_CLASSES = 90

## Load the label map.
# Label maps map indices to category names, so that when the convolution
# network predicts `5`, know that this corresponds to `airplane`.
# Using internal utility functions, but anything that returns a
# dictionary mapping integers to appropriate string labels would be fine
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

# Load the Tensorflow model into memory.
detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

    sess = tf.Session(graph=detection_graph)

# Define input and output tensors (i.e. data) for the object detection classifier
# Input tensor is the image
image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

# Output tensors are the detection boxes, scores, and classes
# Each box represents a part of the image where a particular object was detected
detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

# Each score represents level of confidence for each of the objects.
# The score is shown on the result image, together with the class label.
detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')

# Number of objects detected
num_detections = detection_graph.get_tensor_by_name('num_detections:0')

# Initialize frame rate calculation
frame_rate_calc = 1
freq = cv2.getTickFrequency()
font = cv2.FONT_HERSHEY_SIMPLEX

def specific_detector(frame, dist):
    frame_expanded = np.expand_dims(frame, axis=0)
    # Perform the actual detection by running the model with the image as input
    (boxes, scores, classes, num) = sess.run(
        [detection_boxes, detection_scores, detection_classes, num_detections],
        feed_dict={image_tensor: frame_expanded})

    # Draw the results of the detection; visualize the results
    vis_util.visualize_boxes_and_labels_on_image_array(
        frame,
        np.squeeze(boxes),
        np.squeeze(classes).astype(np.int32),
        np.squeeze(scores),
        category_index,
        use_normalized_coordinates=True,
        line_thickness=8,
        min_score_thresh=0.40)

    # Execute specific actions upon detecting specific objects
    # Object 10 is a traffic light; drive towards it upon detection
    if (int(classes[0][0]) == 10):
        speaker.say("Traffic Light detected. Crossing")
        speaker.runAndWait()
        gpg.drive_cm(20)
    # Object 1 is person; dodges it 25 cm beforehand
    elif ((int(classes[0][0]) == 1) and dist == 25):
        gpg.stop()
        speaker.say("Person detected. Re-routing")
        speaker.runAndWait()
        gpg.orbit(30, 30)
        gpg.orbit(-30, 30)
        gpg.drive_cm(25)
        gpg.stop()
        gpg.turn_degrees(-90)
    # Object 13 is a stop sign; marks the "destination" and stops 25 cm before it
    elif (int(classes[0][0] == 13) and dist == 25):
        speaker.say("Destination reached, stopping.")
        gpg.stop()
    # If above objects not detected GPG advances straight
    else:
        gpg.forward()
    
    return frame

# Starts the PiCamera
def start_camera():
    global camera, rawCapture
    # Initialize camera and perform object detection.
    camera = PiCamera()
    camera.resolution = (IM_WIDTH,IM_HEIGHT)
    camera.framerate = 10
    rawCapture = PiRGBArray(camera, size=(IM_WIDTH,IM_HEIGHT))
    rawCapture.truncate(0)

def start_robot():
    global frame_rate_calc
    speaker.say("Initialising")
    speaker.runAndWait()
    start_camera()

    # Drive towards TL1
    gpg.drive_cm(60)
    gpg.turn_degrees(90)
    gpg.stop()

    # Rely on specific_detector for furthere movements  
    for frame1 in camera.capture_continuous(rawCapture, format="bgr",use_video_port=True):
        dist = dist_sensor.read()
        t1 = cv2.getTickCount()
        
        # Acquire frame and expand frame dimensions to have shape: [1, None, None, 3]
        # i.e. a single-column array, where each item in the column has the pixel RGB value
        frame = np.copy(frame1.array)
        frame.setflags(write=1)
        # frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # frame_expanded = np.expand_dims(frame_rgb, axis=0)

        frame = specific_detector(frame, dist)

        cv2.putText(frame,"FPS: {0:.2f}".format(frame_rate_calc),(30,50),font,1,(255,255,0),2,cv2.LINE_AA)

        # All the results have been drawn on the frame, so it's time to display it.
        cv2.imshow('Object detector', frame)

        t2 = cv2.getTickCount()
        time1 = (t2-t1)/freq
        frame_rate_calc = 1/time1

        # Press 'q' to quit
        if cv2.waitKey(1) == ord('q'):
            break

        rawCapture.truncate(0)

        camera.close()
        
        camera.release()
        cv2.destroyAllWindows()

start_robot()
