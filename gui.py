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
oldMenuY = menuY

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
wheelBGX = int(1104/scaleX)
wheelBGY = int(72/scaleY)
wheelCoverX = int(1142/scaleX)
wheelCoverY = int(268/scaleY)
updateX = int(1148/scaleX)
updateY = int(274/scaleY)
updateDX = int((wheelCoverImg.get_rect().width-16))
updateDY = int((wheelCoverImg.get_rect().height-24))

screen = pygame.display.set_mode((windowWidth,windowHeight),FULLSCREEN|DOUBLEBUF|HWSURFACE)
pygame.display.set_caption('Sykotic Gaming')
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
        if not evt.key == 111:
            if(pygame.mixer.music.get_busy()):
                pygame.mixer.music.stop()
        #print event.key
        if evt.key == 113: # q key
            quitOut()
        elif evt.key == 111: # o key
            launchOptions()
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

def launchOptions():
    global audioMax, audioVolume, childLock, debug
    def procInput(evt):
        if evt.type == KEYDOWN:
            if evt.key == 111: # o key
                return "close"
            elif evt.key == K_UP or evt.key == K_DOWN or evt.key == K_LEFT or evt.key == K_RIGHT or evt.key == K_RETURN:
                return evt.key
                
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
        
        
    optionWidth = updateDX-100
    optionHeight = updateDY
    optionX = (windowWidth/2)-(optionWidth/2)
    optionY = (windowHeight/2)-(optionHeight/2)
    event = pygame.event.poll()
    inputEvent = procInput(event)
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
    option4On = font.render("Exit", 1, (255,255,255))
    option4Off = font.render("Exit", 1, (128,128,128))
    
    resolutions = ["auto","1080p","1600x900","720p","720x480","480p"]
    resolution = 0
    for x in range(0,len(resolutions)):
        if resolutions[x] == settings["resolution"]:
            resolution = x

    optionsOn = [option0On,option1On,option2On,option3On,option4On]
    optionsOff = [option0Off,option1Off,option2Off,option3Off,option4Off]
    selected = 0
    while not (inputEvent == "close"):
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
        fpsClock.tick(FPS)
        event = pygame.event.poll()
        inputEvent = procInput(event)
        if(inputEvent==K_DOWN):
            selected = selected + 1
            if(selected>len(optionsOn)-1):
                selected = 0
        elif(inputEvent==K_UP):
            selected = selected - 1
            if(selected<0):
                selected = len(optionsOn)-1
        elif(inputEvent==K_LEFT or inputEvent==K_RIGHT):
            if(selected==0): #volume
                if(inputEvent==K_LEFT):
                    audioMax = audioMax - 0.01
                else:
                    audioMax = audioMax + 0.01
                audioVolume = audioMax
                pygame.mixer.music.set_volume(audioVolume)
            elif(selected==1): #resolution
                if(inputEvent==K_RIGHT):
                    resolution = resolution + 1
                    if(resolution>len(resolutions)-1):
                        resolution = 0
                else:
                    resolution = resolution - 1
                    if(resolution<0):
                        resolution = len(resolutions)-1
            elif(selected==2): #kids mode
                childLock = not childLock
            elif(selected==3): #kids mode
                debug = not debug
        elif inputEvent==K_RETURN and (selected==(len(optionsOn)-1)):
            inputEvent = "close"
        
    pygame.event.clear()
    settings["resolution"] = resolutions[resolution]
        
def launchGame():
    pygame.event.set_grab(False)
    screen = pygame.display.set_mode((0,0),NOFRAME) # hide my screen
    os.popen(systems[systemID][1] + games[gameID[systemID]][0]) # launch game
    #pygame.event.pump() #tell event that "you're still here"
    pygame.event.clear() #clear out all button pushes
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
    fillWheel(True)

def changeGame(dir):
    global gameID, animateDone, direction, menuY, oldMenuY
    if not animateDone:
        menuY = oldMenuY #reset center
        fillWheel() #load the last selection before more animation
        drawMenu("wheel") #draw the new wheel entries
        #resizeImages()
        #drawScreen()
    else:
        animateDone = False
    gameID[systemID] = gameID[systemID] + (1*dir)
    if gameID[systemID] > len(games)-1:
        gameID[systemID] = 0 # loop
    elif gameID[systemID] < 0:
        gameID[systemID] = len(games)-1 # loop
    oldMenuY = menuY
    direction = dir
    #animateWheel(dir)
    #fillWheel()

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
    lblCommand = tinyfont.render("Command: " + systems[systemID][1] + games[gameID[systemID]][0], 1, (255,255,255))
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
        #a = ((x+1)*25)
        #past[x] = font.render(games[p][1], 1, (180-a,180-a,180-a))
        #futr[x] = font.render(games[f][1], 1, (180-a,180-a,180-a))
        past[x] = font.render(games[p][1][0:30], 1, (255,255,255))
        futr[x] = font.render(games[f][1][0:30], 1, (255,255,255))
    if assests:
        loadAssests()
    
def loadAssests():
    global audioClip, audioVolume, gameBigImg, gameImg
    audioClip = systems[systemID][0] + "/" + games[gameID[systemID]][0] + ".mp3"
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
    
    event = pygame.event.poll()
    procEvents(event)
    
    if not animateDone:
        #print(direction, animateDone)
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