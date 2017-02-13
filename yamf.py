#!/usr/bin/python
"""
This is a MAME / emulator front end built in Python

Created by Jonathan Mayer as the software part of a
personal project. This python program uses the PyGame
library for the graphical user interface and user
input. Joystick controls are the main interface with 
the keyboard as a back up input device.

Roms are stored in the roms folder, split into sub-
folders for each system. All non-arcade emulation is
via the MESS emulator, with the exception of Steam
streaming. 

Image media is organized by EmuMovies Sync and can be
used for free with registration to emumovies.com. No
images are supplied with the program, but can be added
by letting EmuMovies Sync scrap your rom folders.

Audio clips play in the background for the selected 
game. These clips are not supplied with the program 
and must be manually named and placed within system 
sub-folders. Only tested audio codec was mp3.

Available systems and games are loaded from comma 
seperated text files that are created via the rom 
scraper scripts. These files and scripts are accessed 
via the web configuration utility.

"""
# import dependancies
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
from pygame.locals import *
import pygame, sys, os, time, csv, subprocess
from xml.dom import minidom

def debugPrint(msg):
    print(msg.replace("\n","",3))
    with open("debug.txt", 'a') as f:
        f.write(msg + "\n")
# default settings
settings = {"resolution":"auto",
            "width":0,
            "height":0,
            "volume":0.5,
            "childlock":False,
            "wheel":7,
            "debug":False}
            
newpath = os.path.join(os.path.expanduser("~"),"YAMF")
oldpath = os.getcwd()
if(os.getcwd().split('/')[-1]!="YAMF"):
    os.chdir(newpath)

def xmlGet(xml, tag, type="value"):
    if(type=="child"):
        return xml.getElementsByTagName(tag)[0].firstChild.nodeValue
    if(type=="value"):
        return xml.getElementsByTagName(tag)[0].attributes['value'].value

try:
    xmldoc = minidom.parse('settings.xml')
    settings["resolution"] = xmlGet(xmldoc, 'resolution')
    settings["width"] = int(xmlGet(xmldoc, 'width', 'child'))
    settings["height"] = int(xmlGet(xmldoc, 'height', 'child'))
    settings["volume"] = float(xmlGet(xmldoc, 'volume'))
    settings["childlock"] = bool(xmlGet(xmldoc, 'childlock'))
    settings["wheel"] = int(xmlGet(xmldoc, 'wheel'))
    settings["debug"] = bool(xmlGet(xmldoc, 'debug'))
except:
    print("Bad settings.xml file - defaults loaded")
    print("Launch the options menu to rebuild the file")

childLock = settings["childlock"]
audioMax = settings["volume"]
wheelDepth = settings["wheel"] # How many titles to display on each end of current game
if(settings["resolution"]!='auto'): # display resolution overrride
    windowHeight = settings["height"]
    windowWidth = settings["width"]
debug = settings["debug"]
if(debug):
    debugPrint("---" + time.ctime() + "---")

systemID = 0
systems = []

with open("systems.csv", 'r') as systemsFile:
    firstRow = True
    reader = csv.reader(systemsFile, delimiter=',')
    for row in reader:
        if(firstRow):
            firstRow = False
        else:
            systems.append({"info":row, "games":[]})
        
gameID = [0 for x in range(0,len(systems))]
games = []

with open("games.csv", 'r') as gamesFile:
    reader = csv.reader(gamesFile, delimiter=',')
    for row in reader:
        for system in systems:
            if(system["info"][0]==row[0]):
                system["games"].append(row)
                if(system["games"][-1][4]==""):
                    system["games"][-1][4]=system["games"][-1][3]           

pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.init()
pygame.mixer.init()
audioClip = ""
audioVolume = 0
actualFPS = 0

past = [0 for x in range(0,wheelDepth)]
futr = [0 for x in range(0,wheelDepth)]
screen = pygame.display

J_UP = 85
J_DOWN = 68
J_LEFT = 76
J_RIGHT = 82
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
if pygame.joystick.get_count() > 0:
    debugPrint("Number of Joysticks attached: " + str(pygame.joystick.get_count()) + " (listed below)")
else:
    debugPrint("No Joysticks attached")
j = 0
for joystick in joysticks:
    debugPrint("joysticks[" + str(j) + "] = " + joystick.get_name())
    j += 1
    joystick.init()

FPS = 60
fpsClock = pygame.time.Clock()
goodEvent = False
keys = [0] * 512
info = pygame.display.Info()

def loadResolution():
    global txtWidth, menuTitle, menuX, menuY, imgX, imgY, imgBigX, imgBigY
    global menuSpacing, lblChoosen, systemTitle, lblCommand, lblFPS
    global wheelBGX, wheelBGY, wheelCoverX, wheelCoverY, updateX, updateY
    global updateDX, updateDY, scaleX, scaleY, bgImg, fgImg, wheelCoverImg
    global wheelBGImg, wheelFGImg, bigfont, font, tinyfont, windowHeight, windowWidth
    global screen, info
    
    #1080p Resolution - all other resolutions are scaled from this
    bigfont = pygame.font.SysFont("monospace bold", 75)
    font = pygame.font.SysFont("monospace bold", 50)
    tinyfont = pygame.font.SysFont("monospace", 20)
    txtWidth = 320
    menuTitle = 132
    menuX = 1791
    menuY = 600
    imgX = 569
    imgY = 231
    imgBigX = 569
    imgBigY = 673
    menuSpacing = font.get_linesize() + 10
    bgImg = pygame.image.load("assets/bg.png")
    fgImg = pygame.image.load("assets/fg.png")
    gameImg = pygame.image.load("assets/blank.png")
    gameBigImg = pygame.image.load("assets/blank.png")
    wheelCoverImg = pygame.image.load("assets/wheel.png")
    wheelBGImg = pygame.image.load("assets/wheelBG.png")
    wheelFGImg = pygame.image.load("assets/wheelFG.png")
    oldMenuY = menuY

    try:
        windowHeight
        windowWidth
    except:
        windowHeight = info.current_h
        windowWidth = info.current_w
        
    #determine scale from 1080p base
    scaleX = float(1920)/windowWidth
    scaleY = float(1080)/windowHeight
    #resize elements
    bgImg = pygame.transform.scale(bgImg, (windowWidth, windowHeight))
    fgImg = pygame.transform.scale(fgImg, (windowWidth, windowHeight))

    if(windowHeight!=1080):
        wheelCoverImg = pygame.transform.scale(wheelCoverImg, (int(wheelCoverImg.get_rect().width/scaleX),int(wheelCoverImg.get_rect().height/scaleY)))
        wheelBGImg = pygame.transform.scale(wheelBGImg, (int(wheelBGImg.get_rect().width/scaleX), int(wheelBGImg.get_rect().height/scaleY)))
        wheelFGImg = pygame.transform.scale(wheelFGImg, (int(wheelFGImg.get_rect().width/scaleX), int(wheelFGImg.get_rect().height/scaleY)))

    if(debug):
        debugPrint("Resolution changed to: " + str(windowWidth) + "x" + str(windowHeight))

    #adjustments for other resolutions
    if(windowHeight!=1080):
        bigfont = pygame.font.SysFont("monospace bold", int(75/scaleX))
        font = pygame.font.SysFont("monospace bold", int(50/scaleX))
        tinyfont = pygame.font.SysFont("monospace", int(20/scaleX))
        txtWidth = txtWidth/scaleX
        menuTitle = menuTitle/scaleY
        menuX = menuX/scaleX
        menuY = menuY/scaleY
        imgX = imgX/scaleX
        imgY = imgY/scaleY
        imgBigX = imgBigX/scaleX
        imgBigY = imgBigY/scaleY
        menuSpacing = menuSpacing/scaleY
    lblChoosen = bigfont.render("", 1, (255,255,255))
    systemTitle = bigfont.render(systems[systemID]["info"][0], 1, (255,255,255))
    lblCommand = font.render("", 1, (255,255,255))
    lblFPS = font.render("", 1, (255,255,255))
    wheelBGX = int(1104/scaleX)
    wheelBGY = int(72/scaleY)
    wheelCoverX = int(1142/scaleX)
    wheelCoverY = int(268/scaleY)
    updateX = int(1148/scaleX)
    updateY = int(274/scaleY)
    updateDX = int((wheelCoverImg.get_rect().width-16))
    updateDY = int((wheelCoverImg.get_rect().height-24))
    try: # try to load new resolution
        screen = pygame.display.set_mode((windowWidth,windowHeight),FULLSCREEN|DOUBLEBUF|HWSURFACE)
    except: # fallback to desktop resolution
        windowHeight = info.current_h 
        windowWidth = info.current_w
        screen = pygame.display.set_mode((windowWidth,windowHeight),FULLSCREEN|DOUBLEBUF|HWSURFACE)
    pygame.display.set_caption('YAMF')

loadResolution()

animateDone = True
direction = ""

def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step
        
def resizeImages():
    global gameBigImg, gameImg
    height = 222/scaleY
    width = 854/scaleX
    bigHeight = 569/scaleY
    bigWidth = 854/scaleX
    if((float(gameImg.get_rect().height)/gameImg.get_rect().width) > (height/width)): #too tall
        calcHeight = ((gameImg.get_rect().height * width)/(gameImg.get_rect().width))
        gameImg = pygame.transform.scale(gameImg, (int(width), int(calcHeight)))
    else: #too wide
        calcWidth = ((gameImg.get_rect().width * height/gameImg.get_rect().height))
        gameImg = pygame.transform.scale(gameImg, (int(calcWidth), int(height)))
    if((float(gameBigImg.get_rect().height)/gameBigImg.get_rect().width) > (float(bigHeight)/bigWidth)): #too tall
        calcHeight = ((gameBigImg.get_rect().height * bigWidth)/(gameBigImg.get_rect().width))
        gameBigImg = pygame.transform.scale(gameBigImg, (int(bigWidth), int(calcHeight)))
    else: #too wide
        calcWidth = ((gameBigImg.get_rect().width * bigHeight/gameBigImg.get_rect().height))
        gameBigImg = pygame.transform.scale(gameBigImg, (int(calcWidth), int(bigHeight)))
    
def quitOut():
    if(debug):
        debugPrint("DONE: " + str(evtCount) + " Events Total\n\n")
    os.chdir(newpath)
    pygame.quit()
    sys.exit()
    
def clearKeys():
    global keys
    for key in range(0,len(keys)):
        keys[key] = 0
    #for key in keys:
     #   key = 0

def keyMap(evts):
#   QUIT             none
#   ACTIVEEVENT      gain, state
#   KEYDOWN          unicode, key, mod
#   KEYUP            key, mod
#   MOUSEMOTION      pos, rel, buttons
#   MOUSEBUTTONUP    pos, button
#   MOUSEBUTTONDOWN  pos, button
#   JOYAXISMOTION    joy, axis, value
#   JOYBALLMOTION    joy, ball, rel
#   JOYHATMOTION     joy, hat, value
#   JOYBUTTONUP      joy, button
#   JOYBUTTONDOWN    joy, button
#   VIDEORESIZE      size, w, h
#   VIDEOEXPOSE      none
#   SEREVENT        code
    #print(str(pygame.joystick.get_init()))
    for evt in evts:
        global goodEvent, keys
        tick = time.clock()
        goodEvent = False
        if ((evt.type == JOYAXISMOTION) or (evt.type == JOYBUTTONDOWN) or (evt.type == KEYDOWN) or (evt.type == KEYUP)):
            if evt.type == JOYAXISMOTION:
                #print(evt.axis,evt.value)
                if (evt.axis == 1): # Y Axis
                    if (evt.value > .9):
                        keys[J_UP] = 0
                        if keys[J_DOWN] == 0:
                            keys[J_DOWN] = tick
                            goodEvent = True
                    elif (evt.value < -.9):
                        if keys[J_UP] == 0:
                            keys[J_UP] = tick
                            goodEvent = True
                        keys[J_DOWN] = 0
                    else:
                        keys[J_DOWN] = 0
                        keys[J_UP] = 0
                elif (evt.axis == 0): # X Axis
                    if (evt.value > .9):
                        if keys[J_RIGHT] == 0:
                            keys[J_RIGHT] = tick
                            goodEvent = True
                        keys[J_LEFT] = 0
                    elif (evt.value < -.9):
                        keys[J_RIGHT] = 0
                        if keys[J_LEFT] == 0:
                            keys[J_LEFT] = tick
                            goodEvent = True
                    else:
                        keys[J_RIGHT] = 0
                        keys[J_LEFT] = 0
            if evt.type == JOYBUTTONDOWN:
                goodEvent = True
                keys[evt.button] = tick
            elif evt.type == JOYBUTTONUP:
                keys[evt.button] = 0
            if evt.type == KEYDOWN:
                goodEvent = True
                keys[evt.key] = tick
            elif evt.type == KEYUP:
                keys[evt.key] = 0
        elif evt.type == QUIT:
            quitOut()
    
def procEvents():
    global keys
    if (goodEvent) and not (keys[111] or keys[8]): # o key or joystick button 9
        if(pygame.mixer.music.get_busy()):
            pygame.mixer.music.stop()
    if keys[113] or (keys[6] and keys[7]): # q key
        quitOut()
    elif keys[111] or keys[8]: # o key or joystick button 9
        launchOptions()
    if keys[K_UP] or keys[K_DOWN]:
        if keys[K_UP]:
            if (time.clock() - keys[K_UP] > 1.6):
                changeGame(-3)
            else:
                changeGame(-1)
        if keys[K_DOWN]:
            if (time.clock() - keys[K_DOWN] > 1.6):
                changeGame(3)
            else:
                changeGame(1)
    if keys[J_UP] or keys[J_DOWN]:
        if keys[J_UP]:
            if (time.clock() - keys[J_UP] > 1.6):
                changeGame(-3)
            else:
                changeGame(-1)
        if keys[J_DOWN]:
            if (time.clock() - keys[J_DOWN] > 1.6):
                changeGame(3)
            else:
                changeGame(1)
    elif keys[K_LEFT] or keys[K_RIGHT]:
        if keys[K_LEFT]:
            changeSystem(-1)
        else:
            changeSystem(1)
        keys[K_LEFT] = 0
        keys[K_RIGHT] = 0
    if keys[K_RETURN]:
        launchGame()

def launchOptions():
    global audioMax, audioVolume, childLock, debug, windowWidth, windowHeight
    global keys, gameID, repeatTime
    menuOpen = True
    resChanged = False
    kidChanged = False
    clearKeys()
     
    def volBar():
        s3.fill((0,0,0,255), ((optionWidth*.06),(optionHeight*.05)+(menuSpacing*3.2),(optionWidth*.88),menuSpacing))
        s3.fill((255,255,255,255), ((optionWidth*.06),(optionHeight*.05)+(menuSpacing*3.2),(optionWidth*.88)*audioMax,menuSpacing))
        
    def resOptions(): #windowHeight, windowWidth 
        res = font.render(resolutions[resolution], 1, (255,255,255))
        s3.fill((0,0,0,255), ((optionWidth*.30),(optionHeight*.05)+(menuSpacing*5.6),(optionWidth*.4),menuSpacing*.75))
        s3.blit(res, ((optionWidth/2)-res.get_rect().centerx,(optionHeight*.05)+(menuSpacing*5.6),(optionWidth*.88),menuSpacing))
    
    def kidsOption():
        if(childLock):
            on = font.render("ON", 1, (255,255,255))
            off = font.render("OFF", 1, (128,128,128))
        else:
            on = font.render("ON", 1, (128,128,128))
            off = font.render("OFF", 1, (255,255,255))
        s3.blit(on, ((optionWidth*.33)-on.get_rect().centerx,(optionHeight*.05)+(menuSpacing*8.0),(optionWidth*.88),menuSpacing))
        s3.blit(off, ((optionWidth*.66)-off.get_rect().centerx,(optionHeight*.05)+(menuSpacing*8.0),(optionWidth*.88),menuSpacing))
        
    def debugOption():
        if(debug):
            on = font.render("ON", 1, (255,255,255))
            off = font.render("OFF", 1, (128,128,128))
        else:
            on = font.render("ON", 1, (128,128,128))
            off = font.render("OFF", 1, (255,255,255))
        s3.blit(on, ((optionWidth*.33)-on.get_rect().centerx,(optionHeight*.05)+(menuSpacing*10.4),(optionWidth*.88),menuSpacing))
        s3.blit(off, ((optionWidth*.66)-off.get_rect().centerx,(optionHeight*.05)+(menuSpacing*10.4),(optionWidth*.88),menuSpacing))
        
    def saveXML():
        global windowWidth, windowHeight
        with open("settings.xml", 'w') as f:
            f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            f.write("<settings>\n")
            f.write("\t<resolution value=\"" + resolutions[resolution] + "\">\n")
            if(resolutions[resolution]=="TV-1080p"):
                windowWidth = 1920
                windowHeight = 1080
            elif(resolutions[resolution]=="1600x900"):
                windowWidth = 1600
                windowHeight = 900
            elif(resolutions[resolution]=="1440x900"):
                windowWidth = 1440
                windowHeight = 900
            elif(resolutions[resolution]=="TV-720p"):
                windowWidth = 1280
                windowHeight = 720
            elif(resolutions[resolution]=="1024x768"):
                windowWidth = 1024
                windowHeight = 768
            elif(resolutions[resolution]=="720x480"):
                windowWidth = 720
                windowHeight = 480
            elif(resolutions[resolution]=="TV-480p"):
                windowWidth = 640
                windowHeight = 480
            else: #auto
                windowHeight = info.current_h
                windowWidth = info.current_w
            f.write("\t\t<width>" + str(windowWidth) + "</width>\n")
            f.write("\t\t<height>" + str(windowHeight) + "</height>\n")
            f.write("\t</resolution>\n")
            f.write("\t<volume value=\"" + str(audioMax) + "\" />\n")
            if(childLock):
                f.write("\t<childlock value=\"" + str(childLock) + "\" />\n")
            else:
                f.write("\t<childlock value=\"\" />\n")
            f.write("\t<wheel value=\"7\" />\n")
            if(debug):
                f.write("\t<debug value=\"" + str(debug) + "\" />\n")
                debugPrint("---" + time.ctime() + "---")
            else:
                f.write("\t<debug value=\"\" />\n")
                debugPrint("--- Debugging turned off in options ---\n\n")
            f.write("</settings>")
        bigfont = pygame.font.SysFont("monospace bold", int(75/scaleX))
        font = pygame.font.SysFont("monospace bold", int(50/scaleX))
        tinyfont = pygame.font.SysFont("monospace", int(20/scaleX))
    
    optionWidth = updateDX-100
    optionHeight = updateDY
    optionX = (windowWidth/2)-(optionWidth/2)
    optionY = (windowHeight/2)-(optionHeight/2)
    #event = pygame.event.poll()
    event = pygame.event.get()
    keyMap(event)
    s = pygame.Surface((optionWidth, optionHeight), flags=pygame.SRCALPHA)
    s2 = pygame.Surface((optionWidth, optionHeight), flags=pygame.SRCALPHA)
    s.fill((25,200,25,175), (0,0,optionWidth,optionHeight))
    s2.fill((0,0,0,200), (optionWidth*.02,optionHeight*.02,optionWidth-2*(optionWidth*.02),optionHeight-2*(optionHeight*.02)))
    screen.blit(s, (optionX,optionY))
    screen.blit(s2, (optionX,optionY))
    pygame.display.update(optionX,optionY,optionWidth,optionHeight)
    s3 = pygame.Surface((optionWidth, optionHeight), flags=pygame.SRCALPHA)
    spacing = menuSpacing*2.3
    title = font.render("Options Menu", 1, (255,255,255))
    option0On = font.render("Volume", 1, (255,255,255))
    option0Off = font.render("Volume", 1, (128,128,128))
    option1On = font.render("Resolution", 1, (255,255,255))
    option1Off = font.render("Resolution", 1, (128,128,128))
    option2On = font.render("Kids Mode", 1, (255,255,255))
    option2Off = font.render("Kids Mode", 1, (128,128,128))
    option3On = font.render("Debug Mode", 1, (255,255,255))
    option3Off = font.render("Debug Mode", 1, (128,128,128))
    option4On = font.render("Close", 1, (255,255,255))
    option4Off = font.render("Close", 1, (128,128,128))
    
    resolutions = ["auto","TV-1080p","1440x900","1600x900","TV-720p","1024x768","720x480","TV-480p"]
    resolution = 0
    for x in range(0,len(resolutions)):
        if resolutions[x] == settings["resolution"]:
            resolution = x

    optionsOn = [option0On,option1On,option2On,option3On,option4On]
    optionsOff = [option0Off,option1Off,option2Off,option3Off,option4Off]
    selected = 0
    while menuOpen:
        s3.blit(title, ((optionWidth/2)-title.get_rect().centerx,optionHeight*.04))
        for x in range(0,len(optionsOn)):
            if(selected == x):
                s3.blit(optionsOn[x], ((optionWidth/2)-optionsOn[x].get_rect().centerx,(optionHeight*.05)+(spacing*(x+1))))
            else:
                s3.blit(optionsOff[x], ((optionWidth/2)-optionsOff[x].get_rect().centerx,(optionHeight*.05)+(spacing*(x+1))))
        volBar()
        resOptions()
        kidsOption()
        debugOption()
        screen.blit(s3, (optionX,optionY))
        pygame.display.update(optionX,optionY,optionWidth,optionHeight)
        fpsClock.tick(8)
        #event = pygame.event.poll()
        event = pygame.event.get()
        keyMap(event)
        if(keys[K_DOWN]):
            selected = selected + 1
            if(selected>len(optionsOn)-1):
                selected = 0
        elif(keys[K_UP]):
            selected = selected - 1
            if(selected<0):
                selected = len(optionsOn)-1
        elif(keys[K_LEFT] or keys[K_RIGHT]):
            if(selected==0): #volume
                if(keys[K_LEFT]):
                    if(time.clock() - keys[K_LEFT] > 0.8):
                        audioMax = audioMax - 0.05
                    else:
                        audioMax = audioMax - 0.01
                else:
                    if(time.clock() - keys[K_RIGHT] > 0.8):
                        audioMax = audioMax + 0.05
                    else:
                        audioMax = audioMax + 0.01
                if(audioMax < 0): audioMax = 0
                if(audioMax > 1): audioMax = 1
                audioVolume = audioMax
                pygame.mixer.music.set_volume(audioVolume)
            elif(selected==1): #resolution
                resChanged = True
                if(keys[K_RIGHT]):
                    resolution = resolution + 1
                    if(resolution>len(resolutions)-1):
                        resolution = 0
                else:
                    resolution = resolution - 1
                    if(resolution<0):
                        resolution = len(resolutions)-1
            elif(selected==2): #kids mode
                kidChanged = True
                if keys[K_LEFT]:
                    childLock = True
                if keys[K_RIGHT]:
                    childLock = False
            elif(selected==3): #debug mode
                if keys[K_LEFT]:
                    debug = True
                if keys[K_RIGHT]:
                    debug = False
        elif keys[111] or keys[8] or (keys[K_RETURN] and (selected==(len(optionsOn)-1))):
            menuOpen = False
            keys[111] = 0
            keys[8] = 0
            keys[K_RETURN] = 0
        
    pygame.event.clear()
    settings["resolution"] = resolutions[resolution]
    saveXML()
    if(resChanged):
        loadResolution()
    if(resChanged or kidChanged):
        gameID[systemID] = 0
        changeSystem(0) #refresh game list in case kids mode changed
        resizeImages()
    drawScreen()
    
def launchGame():
    if(debug):
        debugPrint("game launch - " + systems[systemID]["info"][1] + games[gameID[systemID]][1])
        timeStart = time.time()
    pygame.event.set_grab(False)
    screen = pygame.display.set_mode((0,0),NOFRAME) # hide my screen
    #os.popen(systems[systemID]["info"][1] + games[gameID[systemID]][1]) # launch game
    subprocess.call(systems[systemID]["info"][1] + games[gameID[systemID]][1]) # launch game
    #pygame.event.pump() #tell event that "you're still here"
    if(debug):
        timeStop = time.time()
        debugPrint("returned after " + str((timeStop - timeStart)/100) + " seconds")
    pygame.event.clear() #clear out all button pushes
    clearKeys() #clear out all key states
    time.sleep(1.5) # give time to recover
    screen = pygame.display.set_mode((windowWidth,windowHeight),FULLSCREEN|DOUBLEBUF|HWSURFACE)
    pygame.event.set_grab(True)
    fillWheel(True)
    resizeImages()
    drawScreen()
    
def changeSystem(dir):
    global systems, systemID, systemTitle, games, gameID
    systemID = systemID + (1*dir)
    if systemID > len(systems)-1:
        systemID = 0 # loop
    elif systemID < 0:
        systemID = len(systems)-1 # loop
    systemTitle = bigfont.render(systems[systemID]["info"][0].replace("_"," "), 1, (255,255,255))
    games = []
    for game in systems[systemID]["games"]:
        if(childLock):
            if(len(game)==6):
                if(game[5]=="Kids"):
                    games.append(game)
        else:
            games.append(game)
    if(len(games)>1):
        games = sorted(games, key=lambda games: games[4].lower())
    fillWheel(True)

def changeGame(dir):
    global gameID, animateDone, direction, menuY, oldMenuY, repeatTime
    if((time.time()-repeatTime)>=0.15):
        if not animateDone:
            menuY = oldMenuY #reset center
            fillWheel() #load the last selection before more animation
            drawMenu("wheel") #draw the new wheel entries
        else:
            animateDone = False
        gameID[systemID] = gameID[systemID] + (1*dir)
        if gameID[systemID] > len(games)-1:
            gameID[systemID] = 0 # loop
        elif gameID[systemID] < 0:
            gameID[systemID] = len(games)-1 # loop
        oldMenuY = menuY
        direction = dir
        repeatTime = time.time()
    #fpsClock.tick(15) #slow it down for key repeat

def animateWheel(dir):
    global menuY, animateDone
    step = (menuSpacing/6)+0.0001 #exactly 6 steps
    step = (dir * -step)
    menuY = menuY + step
    screen.blit(wheelBGImg, (wheelBGX,wheelBGY))
    drawMenu("wheel")
    screen.blit(wheelCoverImg, (wheelCoverX,wheelCoverY))
    pygame.display.update(updateX,updateY,updateDX,updateDY)
    if((dir < 0) and (menuY >= (oldMenuY + menuSpacing))) or ((dir > 0) and (menuY <= (oldMenuY - menuSpacing))):
        animateDone = True
        menuY = oldMenuY
        fillWheel(True)
        drawMenu("wheel")
        resizeImages()
        drawScreen()

def fillWheel(assests=False):
    global lblChoosen, lblCommand
    global past, futr
    lblCommand = tinyfont.render("Command: " + systems[systemID]["info"][1] + games[gameID[systemID]][1] + "." + games[gameID[systemID]][2], 1, (255,255,255))
    p = gameID[systemID]
    f = gameID[systemID]
    lblChoosen = font.render(games[gameID[systemID]][3][0:30], 1, (255,255,255))
    for x in range(0,len(past)):
        p -= 1
        f += 1
        if p < 0:
            p = len(games)-1
        elif p > len(games)-1:
            p = 0
        if f < 0:
            f = len(games)-1
        elif f > len(games)-1:
            f = 0
        past[x] = font.render(games[p][3][0:30], 1, (255,255,255))
        futr[x] = font.render(games[f][3][0:30], 1, (255,255,255))
    if assests:
        loadAssests()
    
def loadAssests():
    global audioClip, audioVolume, gameBigImg, gameImg
    audioClip = "audio/" + systems[systemID]["info"][0] + "/" + games[gameID[systemID]][1] + ".mp3"
    try:
        gameImg = pygame.image.load("media/" + systems[systemID]["info"][0] + "/Marquee/" + games[gameID[systemID]][1] + ".png")
    except:
        try:
            gameImg = pygame.image.load("media/" + systems[systemID]["info"][0] + "/System_Logo/System_Logo.png")
        except:
            try:
                gameImg = pygame.image.load(systems[systemID]["info"][0] + "/" + games[gameID[systemID]][1] + ".gif")
            except:
                gameImg = pygame.image.load("assets/none.png")
    try:
        gameBigImg = pygame.image.load("media/" + systems[systemID]["info"][0] + "/Snap/" + games[gameID[systemID]][1] + ".png")
    except:
        try:
            gameBigImg = pygame.image.load("media/" + systems[systemID]["info"][0] + "/Box/" + games[gameID[systemID]][1] + ".png")
        except:
            try:
                gameBigImg = pygame.image.load(systems[systemID]["info"][0] + "/" + games[gameID[systemID]][1] + "-big.gif")
            except:
                gameBigImg = pygame.image.load("assets/none.png")
    try:
        audioVolume = 0.01
        pygame.mixer.music.load(audioClip)
        pygame.mixer.music.set_volume(audioVolume)
        pygame.mixer.music.play(1) # (3) to play 3 times
    except:
        #print("error loading audio file", audioClip)
        audioVolume = 0
        #pygame.mixer.music.load("assets/blank.mp3")

def drawMenu(type):
    if type == "wheel":
        global screen
        screen.blit(lblChoosen, (((menuX-txtWidth)-lblChoosen.get_rect().centerx), menuY))
        for x in range(0,len(past)):
            screen.blit(past[x], (((menuX-txtWidth)-past[x].get_rect().centerx), (menuY)-((x+1)*menuSpacing)))
            screen.blit(futr[x], (((menuX-txtWidth)-futr[x].get_rect().centerx), (menuY)+((x+1)*menuSpacing)))

def drawScreen():
    # wipe screen black background
    screen.fill((50,50,50))
    screen.blit(bgImg, (0,0))
    screen.blit(gameBigImg, (imgBigX-(gameBigImg.get_rect().centerx),(imgBigY-(gameBigImg.get_rect().centery))))
    screen.blit(gameImg, (imgX-(gameImg.get_rect().centerx),imgY-(gameImg.get_rect().centery)))
    
    #wheel
    drawMenu("wheel")
    if(windowHeight==1080):
        screen.blit(wheelCoverImg, (1142,268))
    else:
        screen.blit(wheelCoverImg, (1142/scaleX,268/scaleY))
    screen.blit(lblChoosen, (((menuX-txtWidth)-lblChoosen.get_rect().centerx), menuY))
    screen.blit(fgImg, (0,0))
    if(debug):
        screen.blit(lblCommand, (10,windowHeight-25))
    screen.blit(systemTitle, (((menuX-txtWidth)-systemTitle.get_rect().centerx), (menuTitle)))
    pygame.display.flip()
    
repeatTime = time.time()
fadeStep = time.time()    
def fadeIn(step, max):
    global audioVolume, fadeStep
    #if(pygame.mixer.music.get_busy()):
    audioVolume = audioVolume + step
    if(audioVolume<=max):
        pygame.mixer.music.set_volume(audioVolume)
        fadeStep = time.time()
        
changeSystem(0)
fillWheel(True) # fill wheel with games
evtCount = 0
resizeImages()
drawScreen()
pygame.event.set_grab(True)
timeStart = time.time()
while True:
    if(debug):
        timeStop = time.time()
        if((timeStop - timeStart)!=0):
            actualFPS = int((actualFPS + (60/((timeStop - timeStart)/0.016666667)))/2)
        timeStart = time.time()
    
    #event = pygame.event.poll()
    event = pygame.event.get()
    keyMap(event)
    procEvents()

    if not animateDone:
        animateWheel(direction)

    if(audioVolume!=0 and audioVolume!=audioMax):
        if(time.time()-fadeStep >= 0.1):
            fadeIn((audioMax/50), audioMax)

    if(goodEvent):
        evtCount += 1
        resizeImages()
        drawScreen()

    fpsClock.tick(FPS)
    
    if(debug):
        lblFPS = tinyfont.render(str(actualFPS) + " fps", 1, (255,255,255))
        screen.fill((0,0,0), (9,windowHeight-49,80,20))
        screen.blit(lblFPS, (10,windowHeight-50))
        pygame.display.update(9,windowHeight-49,80,20)