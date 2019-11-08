import easygopigo3 as EasyGoPiGo3
import time
import pyttsx3

gpg = EasyGoPiGo3.EasyGoPiGo3()
speaker = pyttsx3.init()

# Drive to TL1
gpg.drive_cm(60, True)
gpg.stop()
gpg.turn_degrees(90)
# gpg.orbit(90, 10)

# Sees TL2
speaker.say("Traffic light detected, green light is on")

# Drive towards TL2
gpg.drive_cm(60, True)
gpg.stop()

# Sees person
speaker.say("Person detected, rerouting")

# Divert away from person
gpg.orbit(30, 60)
gpg.stop()

# Stops at TL2, turn and move to destination
gpg.turn_degrees(-90)
# gpg.orbit(-90, 10)
gpg.drive_cm(60, True)
