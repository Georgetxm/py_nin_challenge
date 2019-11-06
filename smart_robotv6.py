import easygopigo3 as EasyGoPiGo3
import time

#set global variables
SCAN_DEGREES = 20 #degrees for servo to turn
MIN_FWD_DISTANCE= 25#treshold of distance (cm) of object ahead before robot stop
MIN_SIDE_DISTANCE =50 #treshold of distance (cm) of object around robot before robot stops
MOVE_FORWARD = True #boolean variable for robot to move forward
MOVE_BACKWARD = False #boolean variable for robot to move backward
 
#initialise distance sensor
GOPIGO3 = EasyGoPiGo3.EasyGoPiGo3()
DISTANCE_SENSOR=GOPIGO3.init_distance_sensor()

#initialise robot
servo1 = GOPIGO3.init_servo("SERVO1")
servo1.rotate_servo (90)
time.sleep(0.5)

#define turn logic function.
def turn_decision(degree_range):
    GOPIGO3.stop()
    global SCAN_DEGREES
    
    if (degree_range == "180"):
        READ_AMOUNT = ((180/SCAN_DEGREES)+1) #how many times the distance sensor has to scan from 0 to 180 degress per SCAN_DEGREES value
        GPG_TURN_DEGREES = -90 #-90 is the amount of degrees the robot has to turn to for a left turn_degrees
        SERVO_DEGREES = 180
       
    elif (degree_range == ("-90")): #negative 90 turn is left
        READ_AMOUNT = (90/SCAN_DEGREES) #how many times the distance sensor has to scan from 0 to 180 degress per SCAN_DEGREES value
        GPG_TURN_DEGREES = -90 #-90 is the amount of degrees the robot has to turn to for a left turn_degrees
        SERVO_DEGREES = 180
    
    elif (degree_range == "90"): #positive 90 degrees turn is right
        READ_AMOUNT = (90/SCAN_DEGREES) #how many times the distance sensor has to scan from 0 to 180 degress per SCAN_DEGREES value
        GPG_TURN_DEGREES = 0 + SCAN_DEGREES #0 is for the robot to move front, thus at scan degrees as we dont want robot to go back to where it was stuck
        SERVO_DEGREES = 90 + SCAN_DEGREES #for servo to scan not directly fron of the robot but at an angle.

    DISTANCE_ARRAY = [] #array to store the value of the distance read by the distance sensor for every incremental degrees(based on SCAN_DEGREES)
    TURN_ARRAY = [] #array to store the vaules the degrees the robot to turn based on the SCAN_DEGREES value
    CHECK_STATUS = True

    for i in range(int(READ_AMOUNT)): #loop for the distance sensor to scan the distance from 0 to 180 and store it in an array
        servo1.rotate_servo(SERVO_DEGREES)
        DISTANCE_CHECK = DISTANCE_SENSOR.read()
        time.sleep(0.2)
        DISTANCE_ARRAY.append(DISTANCE_CHECK)
        TURN_ARRAY.append(GPG_TURN_DEGREES)
        SERVO_DEGREES = SERVO_DEGREES - SCAN_DEGREES
        GPG_TURN_DEGREES = GPG_TURN_DEGREES + SCAN_DEGREES    
        
    servo1.rotate_servo(90)

    while CHECK_STATUS: # loop to check if 20 degrees to the sides of the sensor has enough distance for the robot to clear
        
        DISTANCE_CHECK_INDEX = DISTANCE_ARRAY.index(max(DISTANCE_ARRAY)) #get the index in the distance array of the highest element in the array 
        
        if (DISTANCE_ARRAY[DISTANCE_CHECK_INDEX] > MIN_SIDE_DISTANCE): #condition to check if the max value is more than the treshold distance set

            GOPIGO3.turn_degrees (TURN_ARRAY[DISTANCE_CHECK_INDEX]) #turn the robot to the degrees specified
            servo1.rotate_servo(90) #rotate distance sensor to the default forward position
            time.sleep(0.2)
            servo1.rotate_servo(70)
            RIGHT_DISTANCE = DISTANCE_SENSOR.read()
            time.sleep(0.2)
            servo1.rotate_servo(90)
            time.sleep(0.2)
            servo1.rotate_servo (110)
            LEFT_DISTANCE = DISTANCE_SENSOR.read()
            servo1.rotate_servo(90)
            time.sleep(0.2)
            if (RIGHT_DISTANCE > MIN_SIDE_DISTANCE and LEFT_DISTANCE > MIN_SIDE_DISTANCE):
               
                GO_SIGNAL = "Forward"
                CHECK_STATUS=False
                return GO_SIGNAL
            else:
                
                CHECK_STATUS=False
                #remove max array value and rescan for max and repeat the top process again
                ROTATE_BACK = (TURN_ARRAY[DISTANCE_CHECK_INDEX] * -1)
                GOPIGO3.turn_degrees(ROTATE_BACK)

                if (len(DISTANCE_ARRAY) > 0):
                    CHECK_STATUS = True
                    TURN_ARRAY.pop(DISTANCE_CHECK_INDEX)
                    DISTANCE_ARRAY.pop(DISTANCE_CHECK_INDEX)
                else:
                   
                    CHECK_STATUS=False
                    GO_SIGNAL = "Reverse_Side"
                    return GO_SIGNAL
        else:
            GOPIGO3.stop()
            CHECK_STATUS=False
            GO_SIGNAL = "Reverse"
            return GO_SIGNAL
            

def start_robot():
    global MOVE_FORWARD
    global MOVE_BACKWARD
    
    while MOVE_FORWARD:
        servo1.rotate_servo(90)
        FWD_DISTANCE = DISTANCE_SENSOR.read()
        if FWD_DISTANCE > MIN_FWD_DISTANCE:
            GOPIGO3.forward()
            time.sleep(0.5)
            MOVE_FORWARD = True
            MOVE_BACKWARD = False
        else:   
            GOPIGO3.stop()
            DEGREES_TO_TURN = turn_decision("180") #robot to move check full 180 for valid routes 
            MOVE_FORWARD = False

            if (DEGREES_TO_TURN == "Forward"): #robot to move forward after checking left and right 
                
                GOPIGO3.forward()
                time.sleep(1)
                MOVE_FORWARD = True
                MOVE_BACKWARD = False
            elif (DEGREES_TO_TURN == "Reverse"): #robot to move forward after checking left and right
                GOPIGO3.set_speed(150)
                MOVE_BACKWARD = True
                MOVE_FORWARD = False
                
                while MOVE_BACKWARD: #robot to move backward if no options
                    GOPIGO3.backward()
                    time.sleep(1)
                    
                    servo1.rotate_servo(180)
                    time.sleep(0.2)
                    LEFT_DISTANCE = DISTANCE_SENSOR.read()
                    
                    if (LEFT_DISTANCE > MIN_SIDE_DISTANCE):
                        GOPIGO3.stop()
                    
                    servo1.rotate_servo (0)
                    time.sleep(0.2)
                    RIGHT_DISTANCE = DISTANCE_SENSOR.read()
                    
                    if (RIGHT_DISTANCE > MIN_SIDE_DISTANCE):
                        GOPIGO3.stop()

                    if (RIGHT_DISTANCE > MIN_SIDE_DISTANCE and RIGHT_DISTANCE > LEFT_DISTANCE):
                        REVERSE_SD = turn_decision("90")
                        if (REVERSE_SD == "Forward"):
                            MOVE_BACKWARD = False
                            MOVE_FORWARD = True
                        else:
                            MOVE_BACKWARD = True
                            MOVE_FORWARD = False

                    elif (LEFT_DISTANCE > MIN_SIDE_DISTANCE and LEFT_DISTANCE > RIGHT_DISTANCE):
                        REVERSE_SD = turn_decision("-90")
                        if (REVERSE_SD == "Forward"):
                            MOVE_BACKWARD = False
                            MOVE_FORWARD = True
                        else:
                            MOVE_BACKWARD = True
                            MOVE_FORWARD = False


#set servo to 90 degrees (DISTANCE_SENSOR looking front)
servo1.rotate_servo(90)

#execute code
start_robot()