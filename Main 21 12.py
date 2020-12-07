#Importing and initilising
import pygame, os, time, sqlite3, json
from math import copysign, sin, cos, tan, radians, degrees
from pygame.math import Vector2
pygame.init()

#Setting up variables and filling the window with white
win = pygame.display.set_mode((1546,1007))
font = pygame.font.Font("freesansbold.ttf", 32)
font2 = pygame.font.Font("freesansbold.ttf", 26)
font3 = pygame.font.Font("freesansbold.ttf", 48)
fontTable = pygame.font.SysFont("consolas", 26)
begin = 0
#Font list for the title
fontList = []
for i in range(50):
    fontList.append(pygame.font.Font("freesansbold.ttf", 40 + i))
pygame.display.set_caption("Opus Race")
win.fill((255,255,255))

#Setting the clock for the game so that the fps can be controlled
clock = pygame.time.Clock()

#Setting up the car class
class Car():
    def __init__(self, x, y, vel = 0, accel = 0, angle = 0, maxAccel = 5, brakeDecel = 10, decel = 2, maxVel = 100):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.accel = accel
        self.height = 30
        self.length = 60
        self.angle = angle
        self.maxAccel = maxAccel
        self.brakeDecel = brakeDecel
        self.decel = decel
        self.maxVel = maxVel
                               #This function is not called, and is from prototype 1
                               #It remained here becuase it is useful for debugging however,
    def draw(self, win, rect): #the final version of the code will not incude this
        pygame.draw.rect(win, self.colour, (self.pos.x, self.pos.y, 2, 2))
        pygame.draw.rect(win, self.colour, (self.pos.x + 30 + cos(radians(-self.angle)) * 28,\
                                            self.pos.y + 15 + sin(radians(-self.angle)) * 28, 2, 2))
        pygame.draw.rect(win, self.colour, (self.pos.x + 30 - cos(radians(-self.angle) + 0.4636) * 28,\
                                            self.pos.y + 15 - sin(radians(-self.angle) + 0.4636) * 28, 2, 2))
        pygame.draw.rect(win, self.colour, (self.pos.x + 30 - cos(radians(-self.angle) - 0.4636) * 28,\
                                            self.pos.y + 15 - sin(radians(-self.angle) - 0.4636) * 28, 2, 2))


class Game(): #Setting up the Game class to coordinate the game
    def __init__(self, maxLaps, lapTimes):
        self.trackCount = 0
        self.lineCount = 0
        self.checkCount = 0
        self.reset = False
        self.startTime = 0
        self.start = False
        self.seconds = 0.000
        self.laps = 0
        self.maxLaps = maxLaps
        self.racing = False
        self.finish = False
        self.started = False
        self.finTime = self.seconds
        self.lapTimes = lapTimes
        self.checkpoint = 0
        self.bounce = True
        self.ghosts = False
        self.playGhost = False
        self.ghostCount = {}
        self.ghostNum = 7
        self.track = 1
        self.images = {}
        self.menu = True
        self.titleSpin = 0
        self.spinInc = 1
        self.fontCount = 0
        self.fontInc = 1
        self.pause = False
        self.offsetTime = 0
        self.cars = False
        self.leader = False
        self.timeResult = False
        self.nosTrack = 5

class Button(): #This is the button class used for creating buttons easily
    def __init__(self, x, y, width, height, font, text, colour1, colour2, func=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.text = text
        self.colour1 = colour1
        self.colour2 = colour2
        self.func = func

class CarImage(): #This class allows skins to be selected easily
    def __init__(self, image, x, y, width, height):
        self.image = image
        self.x = x
        self.y = y
        self.width = width
        self.height = height

#Instantiating the game class
maxLaps = 3
lapTimes = []
game = Game(maxLaps, lapTimes)

#Redraws the car and updates the window        
def redraw(dt, all_rows):
    win.fill((255,255,255))
    
    track(game.track)

    #Logic
    if isOnTrack():
        car.maxVel = 100
        car.vel += (car.accel * dt, 0)
        game.trackCount = 0
    elif game.bounce: #Logic for the bounce mechanic
        if game.trackCount == 0:
            car.vel = -car.vel * 0.2  
        game.trackCount += 1
        if game.trackCount > 30:
            game.reset = True
    else: #Logic for the drive over track mechanic
        if car.vel.x > 5:
            car.vel += (-40 * dt, 0)
        else:
            car.vel += (car.accel * dt, 0)
            car.maxVel = 5
    car.pos += car.vel.rotate(-car.angle) * dt

    #This is the check for if the user crosses the finish line with 4 checkpoints passed
    if game.checkpoint == 4:
        if lineCross():
            if game.lineCount == 0:
                if game.started and game.checkpoint == 4:
                    game.finTime = game.seconds
                    if game.lapTimes[0] > 0.0:
                        game.lapTimes[game.laps] = round(game.finTime - sum(game.lapTimes), 3) #Adds lap splits
                    else:
                        game.lapTimes[game.laps] = game.finTime
                    game.laps += 1
            game.checkpoint = 0
            game.lineCount += 1
            if game.laps == game.maxLaps: #Checks if the race is over and stops it if it is
                game.finTime = game.seconds
                game.racing = False
                game.finish = True
        else:
            game.lineCount = 0

    #This is executed if the user crosses a checkpoint
    if checkCross():
        if game.checkCount == 0:
            game.checkpoint += 1 #Adds one to the checkpoint count
        game.checkCount += 1
    else:
        game.checkCount = 0
        

    #Using the max function limits can be set
    car.vel.x = max(-car.maxVel, min(car.vel.x, car.maxVel))
    car.accel = max(-car.maxAccel, min(car.accel, car.maxAccel))

    #Timer and Lap counter
    if game.start:
        game.seconds = (pygame.time.get_ticks() - (game.startTime + game.offsetTime)) / 1000 #Gets the time from the start of the race
#                                                                                             plus the offset time when the game is paused
    timer = font.render(str(int(game.seconds // 60))+":"+str(round(game.seconds % 60, 3)), True, (0, 0, 0)) #Rendering it onto the screen
    for i in range(game.maxLaps):
        lapTime = font2.render(str(int(game.lapTimes[i] // 60))+":"+str(round(game.lapTimes[i] % 60, 3)), True, (50, 50, 50)) #Shows the lap times under the main time
        win.blit(lapTime, (1400, 40 + i * 30))
    lapCount = font.render("LAP "+str(game.laps + 1)+"/"+str(game.maxLaps), True, (0, 0, 0)) #Lap counter
    win.blit(timer, (1400, 10))
    win.blit(lapCount, (25, 10))

    rotated = pygame.transform.rotate(car_image, car.angle)
    rect = rotated.get_rect()
    if game.playGhost and game.start:
        for i in range(0, game.ghostNum + 2):
            try:
                row = all_rows[i][game.ghostCount["g"+str(i+1)]] #Gets the ghost's next move
                rotatedGhost = pygame.transform.rotate(carG_image, int(row[5])) #Same rotation logic for user car and ghost
                rectGhost = rotatedGhost.get_rect()
                win.blit(rotatedGhost, ((float(row[3]) - rect.width / 2) + car.length / 2,\
                                        (float(row[4]) - rect.height / 2) + car.height / 2)) #Displays the ghost's move
                game.ghostCount["g"+str(i+1)] += 1
            except IndexError:
                #game.ghostCount["g"+str(i+1)] -= 1
                game.ghostCount["g"+str(i+1)] = 0 #This line resetst the ghost after every lap, the line above stops them at the finsih line
    rotated = pygame.transform.rotate(car_image, car.angle)
    rect = rotated.get_rect()
    win.blit(rotated, ((car.pos.x - rect.width / 2) + car.length / 2, (car.pos.y - rect.height / 2) + car.height / 2)) #Places the car image on the car object
    pygame.display.update()

def track(num): #Displays different tracks depending on the number passed in, usually game.track
    if num == 1:
        try:
            win.blit(game.images["track1Check"+str(game.checkpoint+1)], (0, 0))
        except KeyError: #If all checkpoints have been crossed this image will not show
            pass
        win.blit(track1Line, (0, 0))
        win.blit(track1_image, (0, 0))
        if game.reset: #Reset positions for this track
            car.angle = 0
            car.pos.x = 550
            car.pos.y = 805
    elif num == 2:
        try:
            win.blit(game.images["track2Check"+str(game.checkpoint+1)], (0, 0))
        except KeyError:
            pass
        win.blit(track2Line, (0, 0))
        win.blit(track2_image, (0, 0))
        if game.reset:
            car.angle = 0
            car.pos.x = 809
            car.pos.y = 830
    elif num == 3:
        try:
            win.blit(game.images["track3Check"+str(game.checkpoint+1)], (0, 0))
        except KeyError:
            pass
        win.blit(track3Line, (0, 0))
        win.blit(track3_image, (0, 0))
        if game.reset:
            car.angle = 0
            car.pos.x = 762
            car.pos.y = 810
    elif num == 4:
        try:
            win.blit(game.images["track4Check"+str(game.checkpoint+1)], (0, 0))
        except KeyError:
            pass
        win.blit(track4Line, (0, 0))
        win.blit(track4_image, (0, 0))
        if game.reset:
            car.angle = 0
            car.pos.x = 939
            car.pos.y = 830
    elif num == 5:
        try:
            win.blit(game.images["track5Check"+str(game.checkpoint+1)], (0, 0))
        except KeyError:
            pass
        win.blit(track5Line, (0, 0))
        if game.checkpoint >= 2:
            win.blit(track52_image, (0, 0)) #The fifth track has two main images to switch
                                            #between when the second checkpoint is crossed
        else:
            win.blit(track51_image, (0, 0))
        if game.reset:
            car.angle = 0
            car.pos.x = 715
            car.pos.y = 767
    if game.reset: #Non-track specific reset values
        car.vel.x = 0
        car.vel.y = 0
        car.accel = 0
        game.seconds = 0.000
        game.laps = 0
        game.start = False
        game.started = False
        game.racing = True
        game.reset = False
        game.finish = False
        game.checkpoint = 0
        game.menu = False
        game.timeResult = True
        for i in range(game.ghostNum):
            game.ghostCount["g"+str(i + 1)] = 0
        for i in range(len(game.lapTimes)):
            game.lapTimes[i] = 0.0

    
def isOnTrack(): #Checks if the car is on the track
    try:
        if game.track == 5: #Only for track 5 as it has two main images
            if game.checkpoint >= 2:
                #The line below checks if the pixel that the car is on on the track is transparent
                if game.images["track"+str(game.track)+"2_image"].get_at((int(car.pos.x + car.length / 2), int(car.pos.y + car.height / 2))).a == 0:
                    return True
                else:
                    return False
            else:
                if game.images["track"+str(game.track)+"1_image"].get_at((int(car.pos.x + car.length / 2), int(car.pos.y + car.height / 2))).a == 0:
                    return True
                else:
                    return False
        else: #For the rest of the tracks
            if game.images["track"+str(game.track)+"_image"].get_at((int(car.pos.x + car.length / 2), int(car.pos.y + car.height / 2))).a == 0:
                return True
            else:
                return False
    except IndexError: #If the car goes off the screen it will be reset
        game.reset = True
        track(game.track)

def lineCross(): #Checks if the car is on/crossing the finsih line with the same logic as the track check
    if game.images["track"+str(game.track)+"Line"].get_at((int(car.pos.x + car.length / 2), int(car.pos.y + car.height / 2))).a != 0:
        return True
    else:
        return False

def checkCross(): #Checks if the car is crossing a checkpoint with the same logic as the track check
    try:
        if game.images["track"+str(game.track)+"Check"+str(game.checkpoint+1)].get_at((int(car.pos.x + car.length / 2), int(car.pos.y + car.height / 2))).a != 0:
            return True
        else:
            return False
    except KeyError: #If all checkpoints have been crossed this will run
        pass

def makeResultsTable(): #Creates the tables for results and splits, only needs to be run once
    db = sqlite3.connect("results.db")
    cursor = db.cursor()
    cursor.execute("""DROP TABLE results""")
    cursor.execute("""DROP TABLE splits""")
    cursor.execute("""CREATE TABLE results (
                    raceID TEXT,
                    track TEXT,
                    time TEXT,
                    laps TEXT);""")
    cursor.execute("""CREATE TABLE splits (
                    raceID TEXT,
                    lapNos TEXT,
                    time TEXT);""")
    db.close()

def makeGhostsTable(): #Creates the table for ghosts, only needs to be run once
    db = sqlite3.connect("ghosts.db")
    cursor = db.cursor()
    cursor.execute("""DROP TABLE ghosts""")
    cursor.execute("""CREATE TABLE ghosts (
                    track TEXT,
                    raceID TEXT,
                    lap TEXT,
                    posX TEXT,
                    posY TEXT,
                    angle TEXT,
                    time TEXT);""")
    db.close()
    
def populateResults(): #Puts the results from a race into the results table
    db = sqlite3.connect("results.db")
    cursor = db.cursor()
    #The section below reads the reults table and gets the highest ID so the next one can be used for the next race
    cursor.execute("""SELECT raceID FROM results""")
    raceID_rows = cursor.fetchall()
    raceID_rowsInt = []
    for i in range(len(raceID_rows)):
        raceID_rowsInt.append(int(raceID_rows[i][0]))
    try:
        ID = int(max(raceID_rowsInt))
    except ValueError:
        ID = 0
    #This section is putting the results and splits into the database
    cursor.execute("""INSERT INTO results VALUES (?, ?, ?, ?)""",\
                   (str(ID + 1), str(game.track), str(game.finTime), str(game.maxLaps)))
    for i in range(game.laps):
        cursor.execute("""INSERT INTO splits VALUES (?, ?, ?)""",\
                       (str(ID + 1), str(i + 1), str(game.lapTimes[i])))
    db.commit()
    db.close()

def populateGhosts(ghostPosListX, ghostPosListY, ghostAngList, lapList): #Populates the ghost table
    db = sqlite3.connect("ghosts.db")
    cursor = db.cursor()
    cursor.execute("""SELECT raceID FROM ghosts WHERE track = ?""", str(game.track))
    raceID_rows = cursor.fetchall()
    try:
        ID = int(max(raceID_rows)[0])
    except ValueError:
        ID = 0
    for i in range(len(ghostPosListX)): #Inserts the value below for every frame of the race
        cursor.execute("""INSERT INTO ghosts VALUES (?, ?, ?, ?, ?, ?, ?)""",\
                       (str(game.track), str(ID + 1), str(lapList[i]), str(ghostPosListX[i]),\
                        str(ghostPosListY[i]), str(ghostAngList[i]), str(game.finTime)))
    print(ID)
    db.commit()
    print("Ghost saved") #Verification that the ghost has been saved
    db.close()

def getGhost(ID): #Gets ghosts from the ghost table for doing a ghost race
    db = sqlite3.connect("ghosts.db")
    cursor = db.cursor()
    #This SQL query gets all from ghosts table which were recorded on that track
    cursor.execute("""SELECT * FROM ghosts WHERE raceID = ? AND track = ?""", (str(ID), str(game.track)))
    all_rows = cursor.fetchall()
    db.close()
    return all_rows

def finPos(): #Calculates the finish position in a ghost race
    db = sqlite3.connect("ghosts.db")
    cursor = db.cursor()
    finTimes = []
    cursor.execute("""SELECT raceID FROM ghosts WHERE track = ?""", str(game.track))
    raceID_rows = cursor.fetchall()
    try:
        ID = int(max(raceID_rows)[0])
    except ValueError:
        ID = 0
    iterations = ID
    if ID >= game.ghostNum:
        iterations = game.ghostNum
    for i in range(1, iterations + 1): #Selects the time of each ghost
        cursor.execute("""SELECT time FROM ghosts WHERE raceID = ? AND track = ?""", (str(i), str(game.track)))
        time = cursor.fetchone()
        finTimes.append(float(time[0]))
    db.close()
    finTimes.append(game.finTime)
    finTimes.sort()
    finPos = finTimes.index(game.finTime) #Returns the position of your time in the sorted list
    return finPos + 1

def timeTrial(): #Sets values to true so that the time will be saved
    game.reset = True
    game.timeResult = True
    track(game.track)

def ghostRace(): #Sets the playGhost to true so that ghosts will be displayed
    car.reset = True
    game.playGhost = True
    game.menu = False
    track(game.track)

def recordGhost(): #Sets values up for recording a ghost
    game.racing = False
    game.menu = False
    car.reset = True
    ghostPosListX = []
    ghostPosListY = []
    ghostAngList = []
    lapList = []
    game.ghosts = True
    track(game.track)

def story(): #Displays the story
    with open("story.txt","r") as story: #Reads from a json file
        lines = json.load(story)
    fadeBack = back2.convert() #Fades the text
    fadeBack.set_alpha(15)
    count = -1
    #Displays the story
    for i in range (0, len(lines) * 300):
        win.blit(fadeBack, (0, 0))
        if i % 300 == 0:
            count += 1
        for j in range(0, len(lines[count])):
            line = font3.render(lines[count][j], True, ((255, 255, 255)))
            win.blit(line, (150, 400 + (j * 200)))
            pygame.display.update()

def cars(): #Sets up values so skins menu is shown
    game.cars = True
    game.menu = False

def leaderBoard(): #Sets up values so leader board is shown
    game.leader = True
    game.menu = False

def sumSplit(sublist): #The key for a .sort function
    newList = []
    for i in range(len(sublist)):
        newList.append(float(sublist[i]))
    return (sum(newList))
                       
#Instantiating a new car and game
car = Car(0,0)
for i in range(maxLaps):
    lapTimes.append(0.0)

#Setting up variables for ghosts
ghostPosListX = []
ghostPosListY = []
ghostAngList = []
lapList = []
all_rows = []
for i in range(1, game.ghostNum + 1):
    all_rows.append(getGhost(i))
#makeGhostsTable()

pauseCount = 0

#Defining buttons
timeTrialButton = Button(200, 350, 300, 175, font, "Time Trial", (255, 0, 0), (0, 255, 0), timeTrial)
ghostRaceButton = Button(625, 350, 300, 175, font, "Ghost Race", (255, 0, 0), (0, 255, 0), ghostRace)
recordGhost = Button(1050, 350, 300, 175, font, "Record Ghost", (255, 0, 0), (0, 255, 0), recordGhost)
storyButton = Button(1050, 700, 300, 175, font, "Story", (255, 0, 0), (0, 255, 0), story)
carsButton = Button(200, 700, 300, 175, font, "Cars", (255, 0, 0), (0, 255, 0), cars)
leaderButton = Button(625, 700, 300, 175, font, "Leader Board", (255, 0, 0), (0, 255, 0), leaderBoard)
buttonList = [timeTrialButton, ghostRaceButton, recordGhost, storyButton, carsButton, leaderButton]

#Setting up images
file_dir = os.path.dirname(os.path.abspath(__file__))

carBlue_image = pygame.image.load(os.path.join(file_dir, "carBlue.png"))
carCrimson_image = pygame.image.load(os.path.join(file_dir, "carCrimson.png"))
carSunset_image = pygame.image.load(os.path.join(file_dir, "carSunset.png"))
carRogue_image = pygame.image.load(os.path.join(file_dir, "carRogue.png"))
carGold_image = pygame.image.load(os.path.join(file_dir, "carGold.png"))
                                                         
carBlue_image = pygame.transform.scale(carBlue_image, (300, 175))
carCrimson_image = pygame.transform.scale(carCrimson_image, (300, 175))
carSunset_image = pygame.transform.scale(carSunset_image, (300, 175))
carRogue_image = pygame.transform.scale(carRogue_image, (300, 175))
carGold_image = pygame.transform.scale(carGold_image, (300, 175))

blueSelect = CarImage(carBlue_image, 100, 250, 300, 175)
crimsonSelect = CarImage(carCrimson_image, 600, 250, 300, 175)
sunsetSelect = CarImage(carSunset_image, 1100, 250, 300, 175)
rogueSelect = CarImage(carRogue_image, 100, 650, 300, 175)
goldSelect = CarImage(carGold_image, 600, 650, 300, 175)

carImages = [blueSelect, crimsonSelect, sunsetSelect, rogueSelect, goldSelect]

car_image = pygame.transform.scale(carBlue_image, (car.length, car.height))

carG_image = pygame.image.load(os.path.join(file_dir, "carOrange.png"))
carG_image = pygame.transform.scale(carG_image, (car.length, car.height))

track1_image = pygame.image.load(os.path.join(file_dir, "track1.png"))
track2_image = pygame.image.load(os.path.join(file_dir, "track2.png"))
track3_image = pygame.image.load(os.path.join(file_dir, "track3.png"))
track4_image = pygame.image.load(os.path.join(file_dir, "track4.png"))
track51_image = pygame.image.load(os.path.join(file_dir, "track5_1.png"))
track52_image = pygame.image.load(os.path.join(file_dir, "track5_2.png"))

track1Line = pygame.image.load(os.path.join(file_dir, "Track1Line.png"))
track2Line = pygame.image.load(os.path.join(file_dir, "Track2Line.png"))
track3Line = pygame.image.load(os.path.join(file_dir, "Track3Line.png"))
track4Line = pygame.image.load(os.path.join(file_dir, "Track4Line.png"))
track5Line = pygame.image.load(os.path.join(file_dir, "Track5Line.png"))

track1Check1 = pygame.image.load(os.path.join(file_dir, "Track1Check1.png"))
track1Check2 = pygame.image.load(os.path.join(file_dir, "Track1Check2.png"))
track1Check3 = pygame.image.load(os.path.join(file_dir, "Track1Check3.png"))
track1Check4 = pygame.image.load(os.path.join(file_dir, "Track1Check4.png"))
track2Check1 = pygame.image.load(os.path.join(file_dir, "Track2Check1.png"))
track2Check2 = pygame.image.load(os.path.join(file_dir, "Track2Check2.png"))
track2Check3 = pygame.image.load(os.path.join(file_dir, "Track2Check3.png"))
track2Check4 = pygame.image.load(os.path.join(file_dir, "Track2Check4.png"))
track3Check1 = pygame.image.load(os.path.join(file_dir, "Track3Check1.png"))
track3Check2 = pygame.image.load(os.path.join(file_dir, "Track3Check2.png"))
track3Check3 = pygame.image.load(os.path.join(file_dir, "Track3Check3.png"))
track3Check4 = pygame.image.load(os.path.join(file_dir, "Track3Check4.png"))
track4Check1 = pygame.image.load(os.path.join(file_dir, "Track4Check1.png"))
track4Check2 = pygame.image.load(os.path.join(file_dir, "Track4Check2.png"))
track4Check3 = pygame.image.load(os.path.join(file_dir, "Track4Check3.png"))
track4Check4 = pygame.image.load(os.path.join(file_dir, "Track4Check4.png"))
track5Check1 = pygame.image.load(os.path.join(file_dir, "Track5Check1.png"))
track5Check2 = pygame.image.load(os.path.join(file_dir, "Track5Check2.png"))
track5Check3 = pygame.image.load(os.path.join(file_dir, "Track5Check3.png"))
track5Check4 = pygame.image.load(os.path.join(file_dir, "Track5Check4.png"))

back1 = pygame.image.load(os.path.join(file_dir, "Back1.png"))
back2 = pygame.image.load(os.path.join(file_dir, "Back2.png"))

#Making a dictionary of the images
game.images = {"track1_image":track1_image, "track2_image":track2_image, "track3_image":track3_image, "track4_image":track4_image, "track51_image":track51_image, "track52_image":track52_image,\
                "track1Line":track1Line, "track2Line":track2Line, "track3Line":track3Line, "track4Line":track4Line, "track5Line":track5Line,\
                "track1Check1":track1Check1, "track1Check2":track1Check2, "track1Check3":track1Check3, "track1Check4":track1Check4,\
                "track2Check1":track2Check1, "track2Check2":track2Check2, "track2Check3":track2Check3, "track2Check4":track2Check4,\
                "track3Check1":track3Check1, "track3Check2":track3Check2, "track3Check3":track3Check3, "track3Check4":track3Check4,\
                "track4Check1":track4Check1, "track4Check2":track4Check2, "track4Check3":track4Check3, "track4Check4":track4Check4,\
                "track5Check1":track5Check1, "track5Check2":track5Check2, "track5Check3":track5Check3, "track5Check4":track5Check4}

#Setting up main game loop
run = True
while run == True:
    clock.tick(144)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    keys = pygame.key.get_pressed()
    
    if game.racing:
        if sum(keys) != 0 and not game.start and game.laps == 0: #Only starts the race once a key is pressed
            game.start = True
            game.started = True
            game.startTime = pygame.time.get_ticks()

        if game.ghosts and game.start: #Starts the ghosts
            ghostPosListX.append(str(car.pos.x))
            ghostPosListY.append(str(car.pos.y))
            ghostAngList.append(car.angle)
            lapList.append(game.laps + 1)
            
        #Setting up delta time so a kinematic model can be used
        dt = clock.get_time() / 200

        #These keys only affect the acceleration which is then appiled to the velocity then
        #position.
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            car.accel += 5 * dt
      
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            car.accel -= 5 * dt

        elif keys[pygame.K_SPACE]:
            if abs(car.vel.x) > dt * car.brakeDecel:
                car.accel = -copysign(car.brakeDecel, car.vel.x)
            else:
                car.accel = -car.vel.x / dt
                
        #If w and s are not being pressed the acceleration is set the the deceleration with
        #the opposite sign to the velocity
        else:
            if abs(car.vel.x) > dt * car.decel:
                car.accel = -copysign(car.decel, car.vel.x)
            else:
                if dt != 0:
                    car.accel = -car.vel.x / dt
                    
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            if game.trackCount == 0:
                car.angle += 5
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            if game.trackCount == 0:
                car.angle -= 5

        #Resets the track
        elif keys[pygame.K_r]:
            game.racing = False
            car.reset = True
            track(game.track)

        #Changes the track
        elif keys[pygame.K_t]: 
            #game.playGhost = False
            game.racing = False
            car.reset = True
            game.track += 1
            if game.track > game.nosTrack:
                game.track = 1
            all_rows = []
            for i in range(1, game.ghostNum + 1):
                all_rows.append(getGhost(i))
            track(game.track)

        #This is for recording a ghost although it is now done through the GUI
        #elif keys[pygame.K_g]:
        #    game.racing = False
        #    car.reset = True
        #    ghostPosListX = []
        #    ghostPosListY = []
        #    ghostAngList = []
        #    lapList = []
        #    game.ghosts = True
        #    track(game.track)

        #Pauses the game
        elif keys[pygame.K_p]:
            game.racing = False
            game.pause = True

        #Returns to the menu
        elif keys[pygame.K_ESCAPE]:
            game.racing = False
            game.menu = True
            
        #dt is passed into redraw because the logic is in that function
        redraw(dt, all_rows)

    #When the race ends
    elif game.finish:
        win.fill((255, 255, 255))
        
        #If in a ghost race the position is shown
        if game.playGhost:
            if finPos() == 1:
                finText = font.render("Finish! You came 1st. Press R to restart", True, (0, 0, 0))
            elif finPos() == 2:
                finText = font.render("Finish! You came 2nd. Press R to restart", True, (0, 0, 0))
            elif finPos() == 3:
                finText = font.render("Finish! You came 3rd. Press R to restart", True, (0, 0, 0))
            else:
                finText = font.render("Finish! You came "+str(finPos())+"th. Press R to restart", True, (0, 0, 0))
        else:
            finText = font.render("Finish! Press R to restart. Your results have been saved.", True, (0, 0, 0))
        finTotTime = font.render("Your time was ["+str(int(game.finTime // 60))+\
                              ":"+str(round(game.finTime % 60, 3))+"] for "+str(i + 1)+" laps", True, (0, 0, 0))
        finSplitText = font2.render("Splits:", True, (0, 0, 0))
        
        #Shows total time and splits
        for i in range(game.maxLaps):
            finSplit = font2.render("Lap "+str(i + 1)+": ["+str(int(game.lapTimes[i] // 60))+\
                              ":"+str(round(game.lapTimes[i] % 60, 3))+"]", True, (0, 0, 0))
            win.blit(finSplit, (680, 490 + i * 30))
        win.blit(finText, (470, 420))
        win.blit(finTotTime, (500, 455))
        win.blit(finSplitText, (590, 490))

        #Restarts the race
        if keys[pygame.K_r]:
            game.reset = True
            game.ghosts = False
            track(game.track)

        #Puts results in the results table
        if game.timeResult and game.lapTimes[0] > 0.0:
            populateResults()
            print("Data has been saved\nTime: "+str(game.finTime)+\
                  " Splits: "+str(game.lapTimes)+" Laps: "+str(game.maxLaps))
            game.timeResult = False
        pygame.display.update()
        #game.playGhost = False

        #Resets the ghost variables
        if game.ghosts:
            populateGhosts(ghostPosListX, ghostPosListY, ghostAngList, lapList)
            ghostPosListX = []
            ghostPosListY = []
            ghostAngList = []
            lapList = []
            game.ghosts = False

    #Menu
    elif game.menu:
        game.playGhost = False
        win.blit(back2, (0, 0))

        #Title
        game.titleSpin += game.spinInc
        if game.titleSpin >= 15:
            game.spinInc = -game.spinInc
        elif game.titleSpin <= -15:
            game.spinInc = -game.spinInc
        game.fontCount += game.fontInc
        if game.fontCount >= len(fontList) - 1:
            game.fontInc = -game.fontInc
        elif game.fontCount <= 0:
            game.fontInc = -game.fontInc
        titleText = fontList[game.fontCount].render("Opus Race", True, (255, 0, 0))
        rotatedText = pygame.transform.rotate(titleText, game.titleSpin)
        rect = rotatedText.get_rect()
        win.blit(rotatedText, (773 - rect.width / 2, 150 - rect.height / 2))

        #Checking for button presses
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        for button in buttonList:
            if button.x + button.width > mouse[0] > button.x and button.y + button.height > mouse[1] > button.y:
                pygame.draw.rect(win, button.colour2, (button.x, button.y, button.width, button.height))
                if click[0] == 1 and button.func() != None:
                    button.func()
            else:
                pygame.draw.rect(win, button.colour1, (button.x, button.y, button.width, button.height))

            textD = font.render(button.text, True, (0, 0, 0))
            textRect = textD.get_rect()
            win.blit(textD, (button.x + button.width/2 - textRect.width/2,\
                                 button.y + button.height/2 - textRect.height/2))
        pygame.display.update()

    #Skin menu
    elif game.cars:
        win.blit(back2, (0, 0))
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        for skin in carImages:
            if skin.x + skin.width > mouse[0] > skin.x and skin.y + skin.height > mouse[1] > skin.y:
                #Could do something when hovering
                if click[0] == 1:
                    car_image = pygame.transform.scale(skin.image, (car.length, car.height))
                    print("Car selected: "+str(skin.image))
                    game.cars = False
                    game.menu = True
                
            win.blit(skin.image, (skin.x, skin.y))
        pygame.display.update()

    #Shows the leader board
    elif game.leader:
        win.blit(back2, (0, 0))
        db = sqlite3.connect("results.db")
        cursor = db.cursor()
        #Gets the the times
        cursor.execute("""SELECT raceID, time FROM results WHERE laps = 3 AND track = ? ORDER BY time ASC""", str(game.track))
        trackTimesID = cursor.fetchall()
        raceIDs = [] #Gets the raceIDs of all the races which satisfy the query
        rawTrackTimes = []
        for i in range(len(trackTimesID)):
            raceIDs.append(trackTimesID[i][0])
            rawTrackTimes.append(float(trackTimesID[i][1]))
        averageTime = round((sum(rawTrackTimes) / len(rawTrackTimes)), 3) #Average race time
        #Gets the splits to do with the raceIDs selected eariler
        cursor.execute("""SELECT time FROM splits WHERE raceID IN (%s)""" % ",".join("?" * len(raceIDs)), raceIDs)
        trackSplits = cursor.fetchall()
        db.close()
        avgSplits = []
        for i in range(3):
            sumSplits = 0
            for j in range(0, int((len(trackSplits)) - 0), 3):
                sumSplits += float(trackSplits[j + i][0])
            avgSplits.append(round((sumSplits / len(trackSplits) * 3), 3)) #Averages the splits
        trackSplitsEdit = []
        for k in range(0, len(trackSplits), 3):
            trackSplitsEdit.append([])
            for p in range(3):
                trackSplitsEdit[int(k / 3)].append(trackSplits[k + p][0])
        trackSplitsEdit.sort(key=sumSplit) #Gets the actual times for the splits
        #Gets the leader board titles ready
        x = 150
        width = 20
        headings = fontTable.render("Position      Time                  Split 1                Split 2                Split 3", True, ((255, 255, 255)))
        whichTrack = font.render("Track "+str(game.track), True, ((255, 255, 255)))
        avgTrackTime = font.render("Average Track Time: "+str(int(averageTime // 60))+\
                              ":"+str(round(averageTime % 60, 3)), True, ((255, 255, 255)))
        avgTrackSplit = font.render("Average Track Splits: "+str(int(avgSplits[0] // 60))+\
                              ":"+str(round(avgSplits[0] % 60, 3))+"     "+str(int(avgSplits[1] // 60))+\
                              ":"+str(round(avgSplits[1] % 60, 3))+"     "+str(int(avgSplits[2] // 60))+\
                              ":"+str(round(avgSplits[2] % 60, 3)), True, ((255, 255, 255)))
        win.blit(headings, (100, 100))
        win.blit(whichTrack, (650, 35))
        win.blit(avgTrackTime, (50, 905))
        win.blit(avgTrackSplit, (50, 940))
        #Formats the data into a table format
        for i in range(len(trackTimesID)):
            if i < 9:
                space = " "
            elif i == 9:
                space = ""
            else:
                break
            leaderTable = fontTable.render(("{} {} {} {} {}".format(str(i + 1)+"      "+space,
                                                                    str(int(float(trackTimesID[i][1]) // 60))+\
                              ":"+str(round(float(trackTimesID[i][1]) % 60, 3)).ljust(width),
                                                                    str(int(float(trackSplitsEdit[i][0]) // 60))+\
                              ":"+str(round(float(trackSplitsEdit[i][0]) % 60, 3)).ljust(width),
                                                                    str(int(float(trackSplitsEdit[i][1]) // 60))+\
                              ":"+str(round(float(trackSplitsEdit[i][1]) % 60, 3)).ljust(width),
                                                                    str(int(float(trackSplitsEdit[i][2]) // 60))+\
                              ":"+str(round(float(trackSplitsEdit[i][2]) % 60, 3)).ljust(width))),
                                           True, ((255, 255, 255)))
            win.blit(leaderTable, (150, x))
            x += 80
        #Returns the to the main menu
        if keys[pygame.K_ESCAPE]:
            game.racing = False
            game.menu = True
            game.leader = False
        pygame.display.update()

    #Pauses the game
    elif game.pause:
        game.offsetTime = pygame.time.get_ticks() - (game.seconds * 1000)
        print(game.offsetTime, pygame.time.get_ticks(), game.seconds * 1000)
        pauseCount += 1
        if pauseCount % 2 == 0:
            if keys[pygame.K_p]:
                game.racing = True
                game.pause = False
        pygame.display.update()
    else:
        game.reset = True
        track(game.track)
pygame.quit()


