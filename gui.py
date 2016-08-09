#!/usr/bin/python

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

import pygame, sys, os, time, csv
from xml.dom import minidom
from pygame.locals import *

#default settings
settings = {"path":u"C:/SykoGame",
            "resolution":"",
            "width":0,
            "height":0,
            "volume":0.5,
            "childlock":False,
            "wheel":7,
            "debug":False}
            
newpath = settings["path"]
oldpath = os.getcwd()
os.chdir(newpath)
try:
    xmldoc = minidom.parse('settings.xml')
    settings["resolution"] = xmldoc.getElementsByTagName('resolution')[0].attributes['value'].value
    settings["width"] = int(xmldoc.getElementsByTagName('width')[0].firstChild.nodeValue)
    settings["height"] = int(xmldoc.getElementsByTagName('height')[0].firstChild.nodeValue)
    settings["volume"] = float(xmldoc.getElementsByTagName('audio')[0].attributes['volume'].value)
    settings["childlock"] = bool(xmldoc.getElementsByTagName('childlock')[0].attributes['value'].value)
    settings["wheel"] = int(xmldoc.getElementsByTagName('wheel')[0].attributes['value'].value)
    settings["debug"] = bool(xmldoc.getElementsByTagName('debug')[0].attributes['value'].value)
except:
    print("Bad settings.xml file - defaults loaded")
    print("Run the settings configuration to rebuild the file")

childLock = settings["childlock"]
audioMax = settings["volume"]
wheelDepth = settings["wheel"] # How many titles to display on each end of current game
if(settings["resolution"]!='auto'): #display resolution overrride
    windowHeight = settings["height"]
    windowWidth = settings["width"]
debug = settings["debug"]


systemID = 0
#gameID = 0
systems = []
with open("systems.csv", 'r') as systemsFile:
    reader = csv.reader(systemsFile, delimiter=',')
    for row in reader:
        systems.append(row)
gameID = [0 for x in range(0,len(systems))]
games = []
with open(systems[systemID][0] + "/games.csv", 'r') as gamesFile:
    reader = csv.reader(gamesFile, delimiter=',')
    for row in reader:
        if(childLock):
            if(row[2]=="Kids"):
                games.append(row)
        else:
            games.append(row)

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()
pygame.mixer.init()
audioClip = ""
audioVolume = 0
actualFPS = 0

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
bgImg = pygame.image.load("bg.png")
fgImg = pygame.image.load("fg.png")
gameImg = pygame.image.load("blank.png")
gameBigImg = pygame.image.load("blank.png")
wheelCoverImg = pygame.image.load("wheel.png")
wheelBGImg = pygame.image.load("wheelBG.png")
wheelFGImg = pygame.image.load("wheelFG.png")

past = [0 for x in range(0,wheelDepth)]
futr = [0 for x in range(0,wheelDepth)]

FPS = 60
fpsClock = pygame.time.Clock()

info = pygame.display.Info()
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
    print("Resolution: " + str(windowWidth) + "x" + str(windowHeight))

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
systemTitle = bigfont.render(systems[systemID][0], 1, (255,255,255))
lblCommand = font.render("", 1, (255,255,255))
lblFPS = font.render("", 1, (255,255,255))
#menuSpacing = font.get_linesize() + 10

screen = pygame.display.set_mode((windowWidth,windowHeight),FULLSCREEN|DOUBLEBUF|HWSURFACE)
pygame.display.set_caption('Sykotic Gaming')

direction = "stop"

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
        print "DONE: " + str(evtCount) + " Events Total"
    os.chdir(newpath)
    pygame.quit()
    sys.exit()
    
def procEvents(evt):
    global goodEvent
    if evt.type == QUIT:
        quitOut()
    elif evt.type == KEYDOWN:
        goodEvent = True
        if(pygame.mixer.music.get_busy()):
            pygame.mixer.music.stop()
        #print event.key
        if evt.key == 113: # q key
            quitOut()
        elif evt.key == K_UP:
            changeGame(-1)
        elif evt.key == K_DOWN:
            changeGame(1)
        elif evt.key == K_LEFT:
            changeSystem(-1)
        elif evt.key == K_RIGHT:
            changeSystem(1)
        elif evt.key == K_RETURN:
            launchGame()
        else:
            if(debug):
                print("unkown input {key:" + str(evt.key) + "}")
    else:
        goodEvent = False

def launchGame():
    pygame.event.set_grab(False)
    screen = pygame.display.set_mode((0,0),NOFRAME) # hide my screen
    os.popen(systems[systemID][1] + games[gameID[systemID]][0]) # launch game
    #pygame.event.pump() #tell event that "you're still here"
    pygame.event.clear() #clear out all button pushes
    time.sleep(1.5) # give time to recover
    screen = pygame.display.set_mode((windowWidth,windowHeight),FULLSCREEN|DOUBLEBUF|HWSURFACE)
    pygame.event.set_grab(True)
    fillWheel()
    resizeImages()
    drawScreen()
    
def changeSystem(dir):
    global systems, systemID, systemTitle, games, gameID
    systemID = systemID + (1*dir)
    if systemID > len(systems)-1:
        systemID = 0 # loop
    elif systemID < 0:
        systemID = len(systems)-1 # loop
    systemTitle = bigfont.render(systems[systemID][0], 1, (255,255,255))
    games = []
    with open(systems[systemID][0] + "/games.csv", 'r') as gamesFile:
        reader = csv.reader(gamesFile, delimiter=',')
        for row in reader:
            if(childLock):
                if(row[2]=="Kids"):
                    games.append(row)
            else:
                games.append(row)
    #gameID = 0
    fillWheel()

def changeGame(dir):
    global gameID
    gameID[systemID] = gameID[systemID] + (1*dir)
    if gameID[systemID] > len(games)-1:
        gameID[systemID] = 0 # loop
    elif gameID[systemID] < 0:
        gameID[systemID] = len(games)-1 # loop
    animateWheel(dir)
    fillWheel()
    
def animateWheel(dir):
    global menuY, actualFPS
    oldMenuY = menuY
    done = False
    #menuY = oldMenuY + 0
    menuStart = time.time()
    step = (menuSpacing/6)+0.0001 #exactly 6 steps
    step = (dir * -step)
    #print("start",menuY)
    wheelBGX = int(1104/scaleX)
    wheelBGY = int(72/scaleY)
    wheelCoverX = int(1142/scaleX)
    wheelCoverY = int(268/scaleY)
    updateX = int(1148/scaleX)
    updateY = int(274/scaleY)
    updateDX = int((wheelCoverImg.get_rect().width-16))
    updateDY = int((wheelCoverImg.get_rect().height-24))
    timeStart = time.time()
    while not done:
        if(debug):
            timeStop = time.time()
            if((timeStop - timeStart)!=0):
                actualFPS = int((actualFPS + (60/((timeStop - timeStart)/0.016666667)))/2)
            timeStart = time.time()
        menuY = menuY + step
        screen.blit(wheelBGImg, (wheelBGX,wheelBGY))
        drawMenu("wheel")
        screen.blit(wheelCoverImg, (wheelCoverX,wheelCoverY))
        pygame.display.update(updateX,updateY,updateDX,updateDY)
        if((dir < 0) and (menuY >= (oldMenuY + menuSpacing))):
            done = True
            #print (menuY, (oldMenuY + menuSpacing))
            menuY = oldMenuY
        elif((dir > 0) and (menuY <= (oldMenuY - menuSpacing))):
            done = True
            #print (menuY, (oldMenuY - menuSpacing))
            menuY = oldMenuY
        fpsClock.tick(FPS)
        if(debug):
            lblFPS = tinyfont.render(str(actualFPS) + " fps", 1, (255,255,255))
            screen.fill((0,0,0), (9,windowHeight-49,80,20))
            screen.blit(lblFPS, (10,windowHeight-50))
            pygame.display.update(9,windowHeight-49,80,20)
    menuStop = time.time()
    actualFPS = int((menuStop - menuStart)*6*60)
    pygame.event.clear()

def fillWheel():
    global gameBigImg, gameImg, lblChoosen, lblCommand
    global past, futr
    global audioClip, audioVolume
    audioClip = systems[systemID][0] + "/" + games[gameID[systemID]][0] + ".mp3"
    lblCommand = tinyfont.render("Command: " + systems[systemID][1] + games[gameID[systemID]][0], 1, (255,255,255))
    try:
        gameImg = pygame.image.load(systems[systemID][0] + "/" + games[gameID[systemID]][0] + ".png")
    except:
        try:
            gameImg = pygame.image.load(systems[systemID][0] + "/" + games[gameID[systemID]][0] + ".jpg")
        except:
            try:
                gameImg = pygame.image.load(systems[systemID][0] + "/" + games[gameID[systemID]][0] + ".gif")
            except:
                #gameImg = pygame.image.load("blank.png")
                gameImg = pygame.image.load(systems[systemID][0] + "/" + systems[systemID][2])
    try:
        gameBigImg = pygame.image.load(systems[systemID][0] + "/" + games[gameID[systemID]][0] + "-big.png")
    except:
        try:
            gameBigImg = pygame.image.load(systems[systemID][0] + "/" + games[gameID[systemID]][0] + "-big.jpg")
        except:
            try:
                gameBigImg = pygame.image.load(systems[systemID][0] + "/" + games[gameID[systemID]][0] + "-big.gif")
            except:
                gameBigImg = pygame.image.load("none.png")
    try:
        audioVolume = 0.01
        pygame.mixer.music.load(audioClip)
        pygame.mixer.music.set_volume(audioVolume)
        pygame.mixer.music.play(1) # (3) to play 3 times
    except:
        print("error loading audio file", audioClip)
        audioVolume = 0
        #pygame.mixer.music.load("blank.mp3")
    p = gameID[systemID]
    f = gameID[systemID]
    lblChoosen = font.render(games[gameID[systemID]][1][0:30], 1, (255,255,255))
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
        a = ((x+1)*25)
        #past[x] = font.render(games[p][1], 1, (180-a,180-a,180-a))
        #futr[x] = font.render(games[f][1], 1, (180-a,180-a,180-a))
        past[x] = font.render(games[p][1][0:30], 1, (255,255,255))
        futr[x] = font.render(games[f][1][0:30], 1, (255,255,255))
    
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
    #screen.blit(gameBigImg, (imgX-(gameBigImg.get_rect().width/2),gameImg.get_rect().height + 20 + imgY))
    
    #wheel
    drawMenu("wheel")
    if(windowHeight==1080):
        screen.blit(wheelCoverImg, (1142,268))
    else:
        screen.blit(wheelCoverImg, (1142/scaleX,268/scaleY))
    screen.blit(lblChoosen, (((menuX-txtWidth)-lblChoosen.get_rect().centerx), menuY))
    #screen.blit(wheelCoverImg, (1000,100))
    screen.blit(fgImg, (0,0))
    if(debug):
        screen.blit(lblCommand, (10,windowHeight-25))
    screen.blit(systemTitle, (((menuX-txtWidth)-systemTitle.get_rect().centerx), (menuTitle)))
    pygame.display.flip()
    
fadeStep = time.time()    
def fadeIn(step, max):
    global audioVolume, fadeStep
    #if(pygame.mixer.music.get_busy()):
    audioVolume = audioVolume + step
    if(audioVolume<=max):
        pygame.mixer.music.set_volume(audioVolume)
        #time.sleep(0.1)
        fadeStep = time.time()
        
fillWheel() # fill wheel with games
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
    
    event = pygame.event.poll()
    procEvents(event)
    
    #if(animate):
    #    animateWheel()
    
    if(audioVolume!=0 and audioVolume!=audioMax):
        if(time.time()-fadeStep >= 0.1):
            fadeIn((audioMax/50), audioMax)
    
    if(goodEvent):
        evtCount += 1
        resizeImages()
        drawScreen()
        #print time.strftime("%H:%M:%S")

    fpsClock.tick(FPS)
    
    if(debug):
        lblFPS = tinyfont.render(str(actualFPS) + " fps", 1, (255,255,255))
        screen.fill((0,0,0), (9,windowHeight-49,80,20))
        screen.blit(lblFPS, (10,windowHeight-50))
        pygame.display.update(9,windowHeight-49,80,20)