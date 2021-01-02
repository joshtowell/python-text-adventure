import json
import time
import datetime as dt
import traceback    ## Allows visual of errors -> traceback.print_exc()

## Name of file containing progress and content
FILENAME = ""

## List for holding game content
CONTENT = []

## Player name as per story
PLAYER = ""

## Head position based on ID
HEAD_POS = 0

## Dictionary for holding game states
STATE = {}

## Printing method bool
SLOWMODE = False

## Menu option lists
MAIN_LIST = ["Play a story", "Write a story", "Quit"]
WRITE_LIST = ["Create a new story", "Load an existing story", "Back"]
LOAD_LIST = ["Load default story", "Load from a known file", "Back"]
PROGRESS_LIST = ["Load progress using player name", "Start a new game", "Back"]

def getInput():
    print("")
    answer = input('>_ ').lower().strip()
    nPrint(1)
    return answer

def nPrint(total):
    for i in range(total):  
        print("")
        time.sleep(0.04)

def sPrint(text):
    global SLOWMODE
    stringList = list(text)
    duration = 0
    if (SLOWMODE):
        duration = 0.04
    for c in stringList:  
        print(c, end = "")
        time.sleep(duration)
    print("")

def showText(textText):
    sPrint(textText + "\n")

def showOptions(options):
    global HEAD_POS
    ordinal = 1
    for opt in options:
        ## Load current option
        optId = opt.get('id')
        optText = opt.get('text')
        optReq = opt.get('requiredState')
        ## Check values present and req passes
        if (optId and optText):
            if (checkAllowedFromReq(optReq)):
                sPrint("[{}] {}".format(ordinal, optText))
                ordinal += 1
        else:
            HEAD_POS = 1
            nPrint(1)
            sPrint("Error loading options. Restarting sequence.")

def getNextText(opt):
    if (opt.get('nextText')):
        return opt.get('nextText')
    else:
        return 0

def checkAllowedFromReq(reqState):
    global STATE
    ## If a state is required
    if (reqState):
        for s in reqState:
            for t in STATE:
                ## If both keys and values match
                if (s == 'inventory'):
                    if (t == s and reqState.get(s) in STATE.get(t)):
                        return True
                else:
                    if (t == s and reqState.get(s) == STATE.get(t)):
                        return True
    ## If no state required
    else:
        return True
    ## If required and not matching
    return False

def updateState(opt):
    global STATE
    optState = opt.get('setState')
    ## If setState is present, apply each state change
    if (optState):
        for req in optState:
            if (req == 'newInventory'):
                if (STATE.get('inventory')):
                    STATE['inventory'].append(optState.get(req))
                else:
                    STATE['inventory'] = [optState.get(req)]
            elif (req == 'removeInventory'):
                if (STATE.get('inventory')):
                    STATE['inventory'].remove(optState.get(req))
            elif (req == 'health'):
                try:
                    if (STATE.get('health')):
                        STATE['health'] = int(STATE.get('health')) + int(optState.get(req))
                    else:
                        STATE['health'] = int(optState.get(req))
                except (ValueError) as e:
                    nPrint(1)
                    sPrint("Error loading state.")
                    sPrint("Error detail (UPDATE1): " + str(e))
            else:
                STATE[req] = optState.get(req)                    

def getOption(options, answer):
    ordinal = 0
    for opt in options:
        optReq = opt.get('requiredState')
        if (checkAllowedFromReq(optReq)):
            ordinal += 1
        ## Locate the chosen option
        if (answer == str(ordinal)):
            return opt

def loadPos(pos):
    global CONTENT
    for obj in CONTENT[0]:
        if (pos == obj.get('id')):
            return obj
    return {}

def startGame():
    global HEAD_POS
    global STATE

    ## Loop whole sequence
    while (HEAD_POS > 0):
        print("INVENTORY:", STATE)  ##TEMP
        ## Load current object
        obj = loadPos(HEAD_POS)
        objText = obj.get('text')
        objOpt = obj.get('options')

        ## Check values present
        if (objText and objOpt):
            showText(objText)
            nextText = 0
            while (nextText < 1):
                showOptions(objOpt)
                answer = getInput()
                chosenOption = getOption(objOpt, answer)
                if (chosenOption):
                    nextText = getNextText(chosenOption)
                    HEAD_POS = nextText
                else:
                    nextText = HEAD_POS
                updateState(chosenOption)
                if (not saveProgress()):
                    nPrint(1)
                    sPrint("Progress save could not be made.")
        else:
            HEAD_POS = 1
            nPrint(1)
            sPrint("Error loading position. Restarting sequence.")

def saveProgress():
    global FILENAME
    global PLAYER
    global STATE
    global HEAD_POS
    try:
        with open(FILENAME + '.json', 'r') as readFile:
            data = readFile.read()
            dataParsed = json.loads(data)
            for player in dataParsed['progress']:
                if (player.get('player') == PLAYER):
                    player['lastPlayed'] = str(dt.datetime.now())
                    player['position'] = HEAD_POS
                    player['state'] = STATE
            try:
                with open(FILENAME + '.json', 'w') as writeFile:
                    json.dump(dataParsed, writeFile)
                return True
            except (json.decoder.JSONDecodeError) as e:
                nPrint(1)
                sPrint("The save file could not be edited.")
                sPrint("Error detail (SAVE2): " + str(e))
                return False
    except (FileNotFoundError) as e:
        nPrint(1)
        sPrint("The save file was not found.")
        sPrint("Error detail (SAVE1): " + str(e))
        return False
    return False

def importProgress(dataParsed):
    global PLAYER
    global STATE
    global HEAD_POS
    answer = ""
    playerName = ""
    playerLoaded = False
    while (not playerLoaded and answer != 'b'):
        showMenu("Player Menu", PROGRESS_LIST)
        answer = getInput()
        try:
            answer = int(answer)
            if (PROGRESS_LIST[answer - 1] == "Load progress using player name"):
                sPrint("Please enter the existing player name...")
                playerName = getInput()
                try:
                    for player in dataParsed['progress']:
                        if (player.get('player') == playerName):
                            HEAD_POS = player.get('position')
                            STATE = player.get('state')
                            PLAYER = playerName
                            playerLoaded = True
                            return playerLoaded
                    nPrint(1)
                    sPrint("This player could not be found.")
                except (json.decoder.JSONDecodeError) as e:
                    nPrint(1)
                    sPrint("This player could not be found.")
                    sPrint("Error detail (LOAD5): " + str(e))
                    return playerLoaded
            elif (PROGRESS_LIST[answer - 1] == "Start a new game"):
                sPrint("Please enter the new player name...")
                playerName = getInput()
                HEAD_POS = 1
                STATE = {}
                PLAYER = playerName
                playerLoaded = True
                return playerLoaded
        except (TypeError, ValueError, IndexError) as e:
            if (answer != 'b'):
                sPrint("Your input was not recognised.")
                sPrint("Error detail (LOAD4): " + str(e))

def importStory():
    global FILENAME
    global LOAD_LIST
    global CONTENT
    filename = ""
    answer = ""
    fileLoaded = False
    while (not fileLoaded and answer != 'b'):
        ## Get filename
        showMenu("Load Menu", LOAD_LIST)
        answer = getInput()
        try:
            answer = int(answer)
            if (LOAD_LIST[answer - 1] == "Load default story"):
                filename = "story"
            elif (LOAD_LIST[answer - 1] == "Load from a known file"):
                sPrint("Please select a story file by entering the file name only...")
                filename = getInput()
            ## Load file
            try:
                with open(filename + '.json', 'r') as myFile:
                    data = myFile.read()
                    try:
                        dataParsed = json.loads(data)
                        CONTENT.append(dataParsed['content'])
                        FILENAME = filename
                        fileLoaded = True
                        playerLoaded = importProgress(dataParsed)
                        return fileLoaded and playerLoaded
                    except (json.decoder.JSONDecodeError) as e:
                        nPrint(1)
                        sPrint("This file could not be read.")
                        sPrint("Error detail (LOAD3): " + str(e))
                        return fileLoaded
            except (FileNotFoundError) as e:
                nPrint(1)
                sPrint("This file was not found.")
                sPrint("Error detail (LOAD2): " + str(e))
                return fileLoaded
        except (TypeError, ValueError, IndexError) as e:
            if (answer != 'b'):
                sPrint("Your input was not recognised.")
                sPrint("Error detail (LOAD1): " + str(e))

def showMenu(menuName, menuList):
    nPrint(2)
    sPrint("===| " + menuName + " |===")
    sPrint("Please select an option:")
    ordinal = 1
    for o in menuList:
        if (o == "Quit"):
            prefix = "q"
        elif (o == "Back"):
            prefix = "b"
        else:
            prefix = str(ordinal)
        sPrint("[{}] {}".format(prefix, o))
        ordinal += 1

def main():
    global MAIN_LIST
    global WRITE_LIST
    answer = ''
    while (not answer == 'q'):
        showMenu("Main Menu", MAIN_LIST)
        answer = getInput()
        try:
            answer = int(answer)
            if (MAIN_LIST[answer - 1] == "Play a story"):
                if (importStory() is True):
                    nPrint(1)
                    startGame()
            elif (MAIN_LIST[answer - 1] == "Write a story"):
                while (not answer == 'b'):
                    showMenu("Write Menu", WRITE_LIST)
                    answer = getInput()
                    try:
                        answer = int(answer)
                        if (WRITE_LIST[answer - 1] == "Create a new story"):
                            sPrint("This feature is still in development.")
                        elif (WRITE_LIST[answer - 1] == "Load an existing story"):
                            sPrint("This feature is still in development.")
                    except (TypeError, ValueError, IndexError) as e:
                        if (answer != 'b'):
                            sPrint("Your input was not recognised.")
                            sPrint("Error detail (WRITE1): " + str(e))
        except (TypeError, ValueError, IndexError) as e:
            if (answer != 'q'):
                sPrint("Your input was not recognised.")
                sPrint("Error detail (MAIN1): " + str(e))
    sPrint("Thanks for playing!")
    nPrint(1)

if __name__ == "__main__":
    main()
