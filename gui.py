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
    
newpath = settings["path"]
oldpath = os.getcwd()
os.chdir(newpath)

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

goodEvent = True
txtWidth = 500
bigfont = pygame.font.SysFont("monospace bold", 35)
font = pygame.font.SysFont("monospace bold", 20)
tinyfont = pygame.font.SysFont("monospace", 10)
menuTitle = 200
gameImg = pygame.image.load("blank.png")
gameBigImg = pygame.image.load("blank.png")
wheelCoverImg = pygame.image.load("wheel.png")

imgX = 10
imgY = 20
imgBigY = 20
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

if(debug):
    print("Resolution: " + str(windowWidth) + "x" + str(windowHeight))
menuX = windowWidth - 880
menuY = windowHeight/2 #centered
#adjustments for common HDTV resolutions
if(windowHeight==1080):
    bigfont = pygame.font.SysFont("monospace bold", 75)
    font = pygame.font.SysFont("monospace bold", 50)
    tinyfont = pygame.font.SysFont("monospace", 20)
    menuTitle = 120
    imgX = 640
    imgY = 200
    imgBigY = 180
if(windowHeight==720):
    bigfont = pygame.font.SysFont("monospace bold", 55)
    font = pygame.font.SysFont("monospace bold", 40)
    tinyfont = pygame.font.SysFont("monospace", 20)
    menuTitle = 60
    imgX = 320
    imgY = 120
    imgBigY = 80
lblChoosen = bigfont.render("", 1, (255,255,255))
systemTitle = bigfont.render(systems[systemID][0], 1, (255,255,255))
lblCommand = font.render("", 1, (255,255,255))
menuSpacing = font.get_linesize() + 10

screen = pygame.display.set_mode((windowWidth,windowHeight),FULLSCREEN)
pygame.display.set_caption('Sykotic Gaming')

direction = "stop"
movie = pygame.movie.Movie('capture.mpg')

def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step

def resizeImages():
    global gameBigImg, gameImg
    if(windowHeight==1080):
        calcHeight = ((gameImg.get_rect().height * 800)/(gameImg.get_rect().width))
        gameImg = pygame.transform.scale(gameImg, (800, calcHeight))
        
        calcWidth = ((gameBigImg.get_rect().width * 600/gameBigImg.get_rect().height))
        gameBigImg = pygame.transform.scale(gameBigImg, (calcWidth, 600))
    if(windowHeight==720):
        #calcWidth = ((gameImg.get_rect().width/gameImg.get_rect().height) * 120)
        #gameImg = pygame.transform.scale(gameImg, (calcWidth, 120))
        calcHeight = ((gameImg.get_rect().height * 500)/(gameImg.get_rect().width))
        gameImg = pygame.transform.scale(gameImg, (500, calcHeight))
        
        calcWidth = ((gameBigImg.get_rect().width * 440/gameBigImg.get_rect().height))
        gameBigImg = pygame.transform.scale(gameBigImg, (calcWidth, 440))

def quitOut():
    if(debug):
        print "DONE: " + str(evtCount) + " Events Total"
    os.chdir(newpath)
    pygame.quit()
    sys.exit()

def loadMovie(filepath):
    global movie
    #pygame.init()
    pygame.mixer.quit()
    pygame.display.init()

    f = BytesIO(open(filepath, 'rb').read())
    movie = pygame.movie.Movie(f)
    #w, h = movie.get_size()
    #w = int(w * 1.3 + 0.5)
    #h = int(h * 1.3 + 0.5)
    w = 500
    h = 350
    cenVid = windowHeight - gameImg.get_rect().height - h
    wsize = (w+10, h+10)
    msize = (w, h)
    #screen = pygame.display.set_mode(wsize)
    movie.set_display(screen, Rect((15, cenVid), msize))

    #pygame.event.set_allowed((QUIT, KEYDOWN))
    #pygame.time.set_timer(USEREVENT, 1000)
    movie.play()
    #while movie.get_busy():
    #    evt = pygame.event.wait()
    #    procEvents(evt)
    #pygame.time.set_timer(USEREVENT, 0)
    
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
    screen = pygame.display.set_mode((windowWidth,windowHeight),FULLSCREEN)
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
    global menuY
    oldMenuY = menuY
    done = False
    menuY = oldMenuY + 0
    while not done:
        menuY = menuY + (dir * -4)
        
        #drawScreen()
        screen.fill((2,22,22),(500,100,windowWidth,windowHeight),0)
        #wheel
        drawMenu("wheel")

        screen.blit(wheelCoverImg, (1000,100))
        
        if(dir < 0):
            if(menuY >= oldMenuY + menuSpacing):
                done = True
                menuY = oldMenuY
        else:
            if(menuY <= oldMenuY - menuSpacing):
                done = True
                menuY = oldMenuY
        pygame.display.update()
        fpsClock.tick(FPS)
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
    lblChoosen = font.render(games[gameID[systemID]][1], 1, (255,255,255))
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
        past[x] = font.render(games[p][1], 1, (255,255,255))
        futr[x] = font.render(games[f][1], 1, (255,255,255))
    
def drawMenu(type):
    if type == "wheel":
        global screen
        screen.blit(lblCommand, (10,windowHeight-25))
        screen.blit(systemTitle, (menuX+(txtWidth-systemTitle.get_rect().centerx), (menuTitle)))
        screen.blit(lblChoosen, (menuX+(txtWidth-lblChoosen.get_rect().centerx), menuY))
        for x in range(0,len(past)):
            screen.blit(past[x], (menuX+(txtWidth-past[x].get_rect().centerx), (menuY)-((x+1)*menuSpacing)))
            screen.blit(futr[x], (menuX+(txtWidth-futr[x].get_rect().centerx), (menuY)+((x+1)*menuSpacing)))

def drawScreen():
    # wipe screen black background
    screen.fill((50,50,50))
    screen.blit(gameBigImg, (imgX-(gameBigImg.get_rect().width/2),imgBigY + imgY))
    screen.blit(gameImg, (imgX-(gameImg.get_rect().width/2),imgY-(gameImg.get_rect().height/2)))
    #screen.blit(gameBigImg, (imgX-(gameBigImg.get_rect().width/2),gameImg.get_rect().height + 20 + imgY))
    
    #wheel
    drawMenu("wheel")

    #screen.blit(wheelCoverImg, (1000,100))
    
    pygame.display.update()
    
        
def fadeIn(step, max):
    global audioVolume
    if(pygame.mixer.music.get_busy()):
        audioVolume = audioVolume + step
        if(audioVolume<=max):
            pygame.mixer.music.set_volume(audioVolume)
            time.sleep(0.1)
        
fillWheel() # fill wheel with games
evtCount = 0
resizeImages()
drawScreen()
pygame.event.set_grab(True)
while True:

    event = pygame.event.poll()
    procEvents(event)
    if(audioVolume!=0 and audioVolume!=audioMax):
        fadeIn((audioMax/50), audioMax)
    
    if(goodEvent):
        evtCount += 1
        resizeImages()
        #wheelCoverImg = pygame.transform.scale(wheelCoverImg, (800, 800))
        drawScreen()
        #if goodEvent:
        #if games[gameID[systemID]][0] == "mk3":
        #    loadMovie("capture.mpg")
        #print time.strftime("%H:%M:%S")

    fpsClock.tick(FPS)
    
