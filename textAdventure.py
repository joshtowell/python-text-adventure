import re
import json
import time
import datetime as dt
import traceback    ## Allows visual of errors -> traceback.print_exc()

## Name of file containing progress and content
FILENAME = ""

## List for holding game content and progress
CONTENT = []
PROGRESS = []

## Player name and save status as per story
PLAYER = "jntowell"     ## TEMP VALUE
PLAYER_SAVED = "new"

## Head position based on ID
HEAD_POS = 0

## Dictionary for holding game states
STATE = {}

## Printing method bool
SLOWMODE = False

## Menu option lists
MAIN_LIST = ["Play a story", "Write a story", "Manage players", "Quit"]
WRITE_LIST = ["Create a new story", "Load an existing story", "Back"]
LOAD_LIST = ["Load default story", "Load from a known file", "Back"]
PROGRESS_LIST = ["Load progress using player name", "Start a new game", "Back"]
MULTISAVE_LIST = ["Overwrite existing progress", "Create a new progress save", "Re-enter player name"]
MANAGE_LIST = ["View player saves", "Delete a player save", "Delete all player saves", "Back"]

def camelCaseSplit(string):
    ## Seperates camel case words into sentence case string
    return re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', string) 

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

def showPlayerState():
    global PLAYER
    global STATE
    sPrint(createBlankLong(len(PLAYER) + 1, char = '='))
    sPrint(PLAYER.upper())
    longest = len(PLAYER)
    for s in STATE:
        totalLength = len(' '.join(camelCaseSplit(s))) + len(str(STATE.get(s))) + 15
        if (totalLength > longest):
            longest = totalLength
    sPrint(createBlankLong(longest + 1, char = '='))
    for s in STATE:
        if (len(camelCaseSplit(s)) > 0):
            key = ' '.join(camelCaseSplit(s))
        else:
            key = s[0].upper() + s[1:]
        sPrint("    " + key + ": " + str(STATE.get(s)))
    sPrint(createBlankLong(longest + 1, char = '='))
    nPrint(1)

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
    sPrint("===")
    sPrint("[q] Quit")

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
    global HEAD_POS
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
            elif (req == 'endGame'):
                if (optState.get('endGame')):
                    return 'q'
            else:
                STATE[req] = optState.get(req)
    return ''

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
    for obj in CONTENT:
        if (pos == obj.get('id')):
            return obj
    return {}

def startGame():
    global HEAD_POS
    global STATE
    global PLAYER

    ## Loop whole sequence
    answer = ""
    while (HEAD_POS > 0 and answer != 'q'):
        nPrint(1)
        ## Show player state
        showPlayerState()
        
        ## Load current object
        obj = loadPos(HEAD_POS)
        objText = obj.get('text')
        objOpt = obj.get('options')

        ## Check values present
        if (objText and objOpt):
            showText(objText)
            nextText = 0
            while (nextText < 1 and answer != 'q'):
                showOptions(objOpt)
                answer = getInput()
                chosenOption = getOption(objOpt, answer)
                if (chosenOption and answer != 'q'):
                    nextText = getNextText(chosenOption)
                    HEAD_POS = nextText
                    ## If end game then answer set to 'q'
                    answer = updateState(chosenOption)
                else:
                    nextText = HEAD_POS
                if (not saveProgress()):
                    nPrint(1)
                    sPrint("Progress save could not be made.")
        else:
            HEAD_POS = 1
            nPrint(1)
            sPrint("Error loading position. Restarting sequence.")
    nPrint(1)
    sPrint("|>>> END OF GAME <<<|")
    
def createNewPlayer(players):
    global PLAYER
    newId = 1
    for player in players:
        if (player.get('id') > newId):
            newId = player.get('id')
    return {"id": newId + 1, "player": PLAYER, "lastPlayed": str(dt.datetime.now()), "position": HEAD_POS, "state": STATE}

def saveProgress():
    global FILENAME
    global PLAYER_SAVED
    global PLAYER
    global STATE
    global HEAD_POS
    try:
        with open(FILENAME + '.json', 'r') as readFile:
            data = readFile.read()
            dataParsed = json.loads(data)
            ## If no player progress at all
            if (len(dataParsed['progress']) < 1):
                dataParsed['progress'].append(createNewPlayer(dataParsed['progress']))
                PLAYER_SAVED = "exists"
            for player in dataParsed['progress']:
                if (player.get('player') == PLAYER):
                    ## Existing player finds existing progress
                    if (PLAYER_SAVED == "exists"):
                        player['lastPlayed'] = str(dt.datetime.now())
                        player['position'] = HEAD_POS
                        player['state'] = STATE
                    ## New player has existing progress
                    elif (PLAYER_SAVED == "new"):
                        showMenu("Save Menu", MULTISAVE_LIST, "There is already a progress save for this player.")
                        answer = getInput()
                        try:
                            answer = int(answer)
                            if (MULTISAVE_LIST[answer - 1] == "Overwrite existing progress"):
                                player['lastPlayed'] = str(dt.datetime.now())
                                player['position'] = HEAD_POS
                                player['state'] = STATE
                                PLAYER_SAVED = "exists"
                            elif (MULTISAVE_LIST[answer - 1] == "Create a new progress save"):
                                existingCount = 0
                                for player in dataParsed['progress']:
                                    if (player.get('player').startswith(PLAYER)):
                                        existingCount += 1
                                PLAYER = PLAYER + str(existingCount + 1)
                                dataParsed['progress'].append(createNewPlayer(dataParsed['progress']))
                                PLAYER_SAVED = "exists"
                            elif (MULTISAVE_LIST[answer - 1] == "Re-enter player name"):
                                sPrint("Please enter the existing player name...")
                                playerName = getInput()
                                try:
                                    for player in dataParsed['progress']:
                                        if (player.get('player') == playerName):
                                            player['lastPlayed'] = str(dt.datetime.now())
                                            player['position'] = HEAD_POS
                                            player['state'] = STATE
                                            PLAYER = playerName
                                            PLAYER_SAVED = "exists"
                                    if (PLAYER_SAVED == "new"):
                                        PLAYER = playerName
                                        dataParsed['progress'].append(createNewPlayer(dataParsed['progress']))
                                        PLAYER_SAVED = "exists"
                                    else:
                                        nPrint(1)
                                        sPrint("This player could not be found.")
                                except (json.decoder.JSONDecodeError) as e:
                                    nPrint(1)
                                    sPrint("This player could not be found.")
                                    sPrint("Error detail (SAVE4): " + str(e))
                                    return False
                        except (TypeError, ValueError, IndexError) as e:
                            sPrint("Your input was not recognised.")
                            sPrint("Error detail (SAVE3): " + str(e))
                            return False
                ## Add new player with no existing progress
                else:
                    if (PLAYER_SAVED == "new"):
                        dataParsed['progress'].append(createNewPlayer(dataParsed['progress']))
                        PLAYER_SAVED = "exists"
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

def importAllData(existFilename = ""):
    global FILENAME
    global LOAD_LIST
    global CONTENT
    global PROGRESS
    filename = ""
    fileLoaded = False
    while (not fileLoaded):
        ## Get filename
        if (len(existFilename) > 0):
            filename = existFilename
        else:
            showMenu("Load Menu", [])
            sPrint("Please select a story file by entering the file name only...")
            filename = getInput()
        ## Load file
        try:
            with open(filename + '.json', 'r') as myFile:
                data = myFile.read()
                try:
                    dataParsed = json.loads(data)
                    CONTENT = dataParsed['content']
                    PROGRESS = dataParsed['progress']
                    FILENAME = filename
                    fileLoaded = True
                    return fileLoaded
                except (json.decoder.JSONDecodeError) as e:
                    nPrint(1)
                    sPrint("This file could not be read.")
                    sPrint("Error detail (DATA2): " + str(e))
                    return fileLoaded
        except (FileNotFoundError) as e:
            nPrint(1)
            sPrint("This file was not found.")
            sPrint("Error detail (DATA1): " + str(e))
            return fileLoaded

def importProgress(dataParsed):
    global PROGRESS_LIST
    global PLAYER_SAVED
    global PLAYER
    global STATE
    global HEAD_POS
    answer = ""
    playerName = ""
    playerLoaded = False
    while (not playerLoaded and answer != 'b'):
        if (len(PLAYER) > 0 and not ( "Load progress using current player" in PROGRESS_LIST)):
            PROGRESS_LIST.insert(0, "Load progress using current player")
        elif (len(PLAYER) < 1 and ("Load progress using current player" in PROGRESS_LIST)):
            PROGRESS_LIST.remove("Load progress using current player")
        showMenu("Player Menu", PROGRESS_LIST)
        answer = getInput()
        try:
            answer = int(answer)
            if (PROGRESS_LIST[answer - 1] == "Load progress using current player"):
                try:
                    for player in dataParsed['progress']:
                        if (player.get('player') == PLAYER):
                            PLAYER_SAVED = "exists"
                            HEAD_POS = player.get('position')
                            STATE = player.get('state')
                            playerLoaded = True
                            return playerLoaded
                    nPrint(1)
                    sPrint("This player could not be found.")
                except (json.decoder.JSONDecodeError) as e:
                    nPrint(1)
                    sPrint("This player could not be found.")
                    sPrint("Error detail (LOAD6): " + str(e))
                    return playerLoaded
            elif (PROGRESS_LIST[answer - 1] == "Load progress using player name"):
                sPrint("Please enter the existing player name...")
                playerName = getInput()
                try:
                    for player in dataParsed['progress']:
                        if (player.get('player') == playerName):
                            PLAYER_SAVED = "exists"
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
                PLAYER_SAVED = "new"
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
                        CONTENT = dataParsed['content']
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

def storyStats():
    global CONTENT
    global PROGRESS
    global FILENAME
    storyName = FILENAME
    numPositions = len(CONTENT)
    numPlayers = len(PROGRESS)
    playerStats = []
    if (numPlayers < 1):
        playerStats = [[" [Empty]", ""]]
    for player in PROGRESS:
        try:
            percent = int((player.get('position') / numPositions) * 100)
            playPercent = ""
            if (percent < 10):
                playPercent = '  '
            elif (percent < 100):
                playPercent = ' '
            playPercent += str(percent) + "%"
        except:
            playPercent = "  0%"
        playerStats.append([player.get('player'), playPercent])
    return {"Story Name": storyName, "Number of Positions": numPositions, "Number of Players": numPlayers, "Player Progression": playerStats}

def playerInfo(player, items = ['name', 'time', 'pos', 'state']):
    global PROGRESS
    for p in PROGRESS:
        if (p.get('player') == player):
            nPrint(1)
            if ('name' in items):
                sPrint("Name: " + p.get('player'))
            if ('time' in items):
                sPrint("Last Played: " + p.get('lastPlayed'))
            if ('pos' in items):
                sPrint("Position: " + str(p.get('position')))
            if ('state' in items):
                sPrint("State:")
                for s in p.get('state'):
                    if (len(camelCaseSplit(s)) > 0):
                        key = ' '.join(camelCaseSplit(s))
                    else:
                        key = s[0].upper() + s[1:]
                    sPrint("    " + key + ": " + str(p.get('state').get(s)))
            return True
    nPrint(1)
    sPrint("This player could not be found.")
    return False

def getPlayerObj(player):
    global PROGRESS
    for p in PROGRESS:
        if (p.get('player') == player):
            return p
    return False

def playerDelete(player):
    global PROGRESS
    global FILENAME
    playerObj = getPlayerObj(player)
    PROGRESS.remove(playerObj)
    try:
        with open(FILENAME + '.json', 'w') as writeFile:
            json.dump({"progress": PROGRESS, "content": CONTENT}, writeFile)
        if (importAllData(FILENAME)):
            return True
    except (json.decoder.JSONDecodeError) as e:
        nPrint(1)
        sPrint("The save file could not be edited.")
        sPrint("Error detail (SAVE2): " + str(e))
        return False
    
def clearProgress():
    global PROGRESS
    global FILENAME
    try:
        with open(FILENAME + '.json', 'w') as writeFile:
            json.dump({"progress": [], "content": CONTENT}, writeFile)
        if (importAllData(FILENAME)):
            return True
    except (json.decoder.JSONDecodeError) as e:
        nPrint(1)
        sPrint("The save file could not be edited.")
        sPrint("Error detail (SAVE2): " + str(e))
        return False

def managePlayers():
    global MANAGE_LIST
    answer = ""
    while (not answer == 'b'):
        showMenu("Manage Menu", MANAGE_LIST, subList = storyStats())
        answer = getInput()
        try:
            answer = int(answer)
            if (MANAGE_LIST[answer - 1] == "View player saves"):
                sPrint("Please enter the existing player name...")
                player = getInput()
                playerInfo(player)
            elif (MANAGE_LIST[answer - 1] == "Delete a player save"):
                sPrint("Please enter the existing player name...")
                player = getInput()
                if (getPlayerObj(player)):
                    sPrint("Are you sure you want to PERMENANTLY DELETE " + player + "'s progress? (yes/no)...")
                    if (getInput() == "yes"):
                        if (not playerDelete(player)):
                            nPrint(1)
                            sPrint("Player progress was unable to be deleted.")
            elif (MANAGE_LIST[answer - 1] == "Delete all player saves"):
                sPrint("Are you sure you want to PERMENANTLY DELETE ALL player progress? (yes/no)...")
                if (getInput() == "yes"):
                    if (not clearProgress()):
                        nPrint(1)
                        sPrint("Progress was unable to be deleted.")
        except (TypeError, ValueError, IndexError) as e:
            if (answer != 'b'):
                sPrint("Your input was not recognised.")
                sPrint("Error detail (MANAGE1): " + str(e))

def saveStory(new = False):
    global FILENAME
    try:
        if (not new):
            with open(FILENAME + '.json', 'r') as readFile:
                data = readFile.read()
                try:
                    dataParsed = json.loads(data)
                    PROGRESS = dataParsed['progress']
                    FILENAME = filename
                except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
                    nPrint(1)
                    sPrint("This file could not be read.")
                    sPrint("Error detail (STORY2): " + str(e))
                    return False
        with open(FILENAME + '.json', 'w') as writeFile:
            if (new):
                json.dump({"progress": [], "content": []}, writeFile)
            else:
                json.dump({"progress": PROGRESS, "content": CONTENT}, writeFile)
        return True
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        nPrint(1)
        sPrint("The save file could not be edited.")
        sPrint("Error detail (STORY1): " + str(e))
        return False

def writeStory():
    global FILENAME
    answer = ''
    while (not answer == 'b'):
        showMenu("Write Menu", WRITE_LIST)
        answer = getInput()
        try:
            answer = int(answer)
            if (WRITE_LIST[answer - 1] == "Create a new story"):
                sPrint("Please enter the file name for your story (no spaces)...")
                filename = getInput()
                FILENAME = filename
                if (not saveStory(True)):
                    nPrint(1)
                    sPrint("File was unable to be created.")
            elif (WRITE_LIST[answer - 1] == "Load an existing story"):
                sPrint("This feature is still in development.")
        except (TypeError, ValueError, IndexError) as e:
            if (answer != 'b'):
                sPrint("Your input was not recognised.")
                sPrint("Error detail (WRITE1): " + str(e))

def createBlankLong(length, char = ' '):
    blank = ""
    for i in range(length):
        blank += char
    return blank

def showMenu(menuName, menuList, subText = "", subList = []):
    global PLAYER
    nPrint(2)
    sPrint("===| " + menuName + " |===")
    if (len(PLAYER) > 0):
        sPrint("Player: " + PLAYER)
    if (len(subText) > 0):
        sPrint(subText)
    if (len(subList) > 0):
        nPrint(1)
        for i in subList:
            if (i == "Player Progression"):
                sPrint(i + ":")
                longest = 0
                for p in subList.get(i):
                    if (len(p[0]) > longest):
                        longest = len(p[0])
                for p in subList.get(i):
                    sPrint("    " + p[0] + createBlankLong(longest + 3 - len(p[0])) + p[1])
            else:
                sPrint(i + ": " + str(subList[i]))
        nPrint(1)
    if (len(menuList) > 0):
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

def mainMenu():
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
                writeStory()
            elif (MAIN_LIST[answer - 1] == "Manage players"):
                if (importAllData() is True):
                    managePlayers()
        except (TypeError, ValueError, IndexError) as e:
            if (answer != 'q'):
                sPrint("Your input was not recognised.")
                sPrint("Error detail (MAIN1): " + str(e))

def main():
    mainMenu()
    sPrint("Thanks for playing!")
    nPrint(1)

if __name__ == "__main__":
    main()
