#! /usr/bin/env python3
# Recreation of DUNGEON, a game written by Brian Sawyer for Cursor Magazine,
# issue #15. Published in Dec 1979. 
# Michael Shorten, June 2020, Public Domain, I have no rights to original
# source. I am doing this for educational purposes to demonstrate computer
# history and what it might look like in modern programming.

from random import random, randint, choice
import sys
from time import sleep
from math import sqrt
import curses

WIDTH = 40
HEIGHT = 23
ROOM_SIZE_MAX = 10
DESIRED_RMS = 8
MONSTERS = ["X","G","D","S","N","W"]
BLANK = " "
FLOOR = "."
DOOR = "+"
GOLD = "g"
NUM_HIDDEN_GOLD = 11
BORDER = "*"
PLAYER = "@"
VALIDMOVES = "qs123456789"
MOVEMAP = [(0,0),(-1,1),(0,1),(1,1),(-1,0),(0,0),(1,0),(-1,-1),(0,-1),(1,-1)]
PRINT_PAUSE = 1
WINDOWS_KEYPAD = ["n/a","key_c1","key_c2","key_c3","key_b1","key_b2",
  "key_b3","key_a1","key_a2","key_a3"]
LINUX_KEYPAD = ["n/a","key_end","key_down","key_npage","key_left",
  "n/a","key_right","key_home","key_up","key_ppage"]
STATUS_ROW = 0
MESSAGE_ROW = 1

class GameState():

    def __init__(self):
        self.dungeon_map = []
        self.player_map = []

        self.hidden_gold = NUM_HIDDEN_GOLD
        self.gold_stash = 0
        self.found_gold = False

        self.whats_here = FLOOR
        self.monster_whats_here = FLOOR
        self.see_more = False
        self.shift_mode = 0

        self.player_locX = 0
        self.player_locY = 0
        self.player_HP = 50
        self.player_gold = 0
        self.player_experience = 0
        self.monsters_killed = 0
        self.next_level = 0

        self.active_monster = ""
        self.monster_name = ""
        self.monster_level = 0
        self.monster_hp = 0
        self.monster_locX = 0
        self.monster_locY = 0
        self.monster_delay = 0
        self.prev_monster = ""


def display_welcome(screen):
    screen.clear()
    screen.addstr("  PYDUNGEON\n A recreation of CURSOR #15 DUNGEON\n")
    screen.addstr("Original (C)1979 by Brian Sawyer.\nPyDungeon is public domain.\n")
    screen.addstr(("-" * 40) + "\n")
    screen.addstr("Search for GOLD in the ancient ruins\n\n")
    screen.addstr("Press ")
    screen.addstr("RETURN", curses.A_REVERSE)
    screen.addstr(" to begin ")
    screen.refresh()
    keystr = ""
    while keystr != "\n" and keystr != "padenter":
        keystr = screen.getkey().lower()


def message_update(screen, msg, reversed=False):
    if reversed:
        attrib = curses.A_REVERSE
    else: 
        attrib = curses.A_NORMAL

    screen.addstr(MESSAGE_ROW, 0, " " * WIDTH)
    screen.addstr(MESSAGE_ROW, 0, msg, attrib)
    screen.refresh()
    sleep(1)


def get_player_move(screen, game_state):
    screen.addstr(STATUS_ROW, 0, 
      "HIT PTS. {}  EXP. {}  GOLD {}".format(
        int(game_state.player_HP+.5), 
        game_state.player_experience, 
        game_state.player_gold))

    move = "X"
    while not move in VALIDMOVES:
        move = get_input(screen, "You may move. ")

    # Check to see if the move is one of the special
    # shift mode values that might occur in windows
    # or linux/unix. If so, set the move to be the
    # keypad number and the game state shift mode to on.
    # otherwise, set shift mode to off.
    if move in WINDOWS_KEYPAD:
        move = str(WINDOWS_KEYPAD.index(move))
        game_state.shift_mode = 1
    elif move in LINUX_KEYPAD:
        move = str(LINUX_KEYPAD.index(move))
        game_state.shift_mode = 1
    else:
        game_state.shift_mode = 0

    return move


def get_input(screen, msg=""):
    if msg != "":
        num_rows, num_cols = screen.getmaxyx()
        str = msg + (" " * (num_cols-len(msg)))
        screen.addstr(MESSAGE_ROW, 0, str)
        screen.move(MESSAGE_ROW, len(msg))
        screen.refresh()
        sleep(.5)
    keystr = ""
    while keystr == "":
        keystr = screen.getkey().lower()

    return keystr


def init_map():
    # Create new map/screen data structure
    # Returns: list of [WIDTH][HEIGHT] elements
    map_struct = []
    for col in range(WIDTH):
        map_struct.append([])
        for row in range(HEIGHT):
            map_struct[col].append(BLANK)

    return map_struct


def generate_rooms(map):

    max_rooms = DESIRED_RMS + choice((-1,0,1))

    # Keep generating rooms until we've hit a limit of DESIRED_RMS(+/- 1) rooms
    for rooms_generated in range(0,max_rooms):
        room_width=0; room_height=0
        roomX=0; roomY=0
        monsterX=0; monsterY=0

        bad_room = True
        while bad_room:
            room_width = randint(2,ROOM_SIZE_MAX)
            room_height = randint(2,ROOM_SIZE_MAX)
            # Starting at 1 because 0 is always the border and we want a gap of
            # at least a space around things.
            roomX = randint(2,WIDTH-1); roomY = randint(2,HEIGHT-1)         

            # Check to see if the room would extend over borders
            if roomX+room_width > WIDTH-2 or roomY+room_height > HEIGHT-2:
                continue        

            # Check to see if room would extend over something already generated
            # We want a gap of at least 1 space between rooms
            overlap = False
            for x in range(roomX-1,roomX+room_width+2):          
                for y in range(roomY-1,roomY+room_height+2):    
                    if map[x][y]!= BLANK:           # is something already here?
                        overlap = True              # then try again
                        break
                if overlap:
                    break
            if overlap:
                continue

            bad_room = False           

        # Fill room floor
        for x in range(roomX,roomX+room_width+1):
            for y in range(roomY,roomY+room_height+1):
                map[x][y] = FLOOR

        # Generate vertical passages from generated room down.
        passageX = roomX + randint(0,room_width)
        for row in range(roomY+room_height+1,HEIGHT-2):
            if map[passageX][row] not in (BLANK, BORDER, DOOR):
                for passageY in range(roomY+room_height+1, row):
                    map[passageX][passageY]=FLOOR
                map[passageX][row-1]=DOOR
                break

        # Generate horizontal passages from generated room right.
        passageY = roomY + randint(0,room_height)
        for col in range(roomX + room_width+1, WIDTH-2):
            if map[col][passageY] not in (BLANK, BORDER, DOOR):
                for passageX in range(roomX+room_width+1,col):
                    map[passageX][passageY]=FLOOR
                map[col-1][passageY]=DOOR
                break

        # Generate a monster in the room. Every room has a monster!
        monsterX = randint(roomX, roomX+room_width)
        monsterY = randint(roomY, roomY+room_height)
        map[monsterX][monsterY] = choice(MONSTERS)


def gen_dungeon():
    # We return a list data structure that represents a map of 40 columns, 
    # 25 rows. The dungeon is generated inside this structure and serves
    # to feed what will be seen on the screen. In a sense, we'll have two 
    # structures - the full map, and then the map that the player reveals 
    # and what gets painted to the screen.
    # See "dungeon-memory-sim.py" for my notes on how this all worked in the
    # original source. I've since "pythonized" the code to reflect the data
    # structures I'm working with, instead of a memory<->screen mapping that 
    # the original program worked with.
    map = []
    map = init_map()

    # Create border around map
    for x in range(0,WIDTH):
        for y in range(0,HEIGHT):
            if x==0 or y==0 or x==WIDTH-1 or y==HEIGHT-1:
                map[x][y]=BORDER

    generate_rooms(map)

    # Distribute 11 gold around the dungeon
    for N in range(1, NUM_HIDDEN_GOLD+1):
        is_floor = False
        while not is_floor:
            goldX = randint(1,WIDTH-1); goldY = randint(1,HEIGHT-1)
            is_floor = (map[goldX][goldY]==FLOOR)
        map[goldX][goldY]=GOLD

    return map


def what_is_seen(screen, game_state):

    gold_near = False

    if game_state.see_more:
        distance = 2; game_state.see_more = False
    else:
        distance = 1

    for x in range(distance*-1, distance+1):
        for y in range(distance*-1, distance+1):
            viewx = game_state.player_locX + x
            viewy = game_state.player_locY + y

            # If we're trying to view off map, or our current position, 
            # continue on.
            if viewx < 1 or viewy < 1 or \
               viewx > 39 or viewy > 39 or (x==0 and y==0):
                continue

            whats_here = game_state.dungeon_map[viewx][viewy]
            game_state.player_map[viewx][viewy] = whats_here

            if whats_here in (DOOR, FLOOR, BORDER):
                continue
            if whats_here==GOLD:
                # We found gold! How much?
                game_state.gold_stash += 1+int(
                    (game_state.player_gold+1)*(random()))  
                gold_near = True
                # If we've not been near this gold, announce it.
                if not game_state.found_gold:
                    message_update(screen, "Gold is near!")
                continue
            if whats_here in MONSTERS:
                if whats_here=="X":
                    game_state.monster_name="Spider"
                    game_state.monster_level=3
                elif whats_here=="G":
                    game_state.monster_name="Grue"
                    game_state.monster_level=7
                elif whats_here=="D":
                    game_state.monster_name="Dragon"
                    game_state.monster_level=1
                elif whats_here=="S":
                    game_state.monster_name="Snake"
                    game_state.monster_level=2
                elif whats_here=="N":
                    game_state.monster_name="Nuibus"
                    game_state.monster_level=9
                elif whats_here=="W":
                    game_state.monster_name="Wyvern"
                    game_state.monster_level=5

                game_state.active_monster = whats_here
                game_state.dungeon_map[viewx][viewy] = FLOOR
                game_state.monster_delay = 0

                # Monster HP based on our HP, experience and random
                # We save the level for later if we defeat the monster, to 
                # get XP from!
                # HP will change each time we see this monster. Heh.
                game_state.monster_hp = game_state.monster_level = \
                    int(random()*game_state.player_HP + 
                     (game_state.player_experience/game_state.monster_level) + 
                     game_state.player_HP/4)

                # If we've already revealed a monster, put it back on the
                # dungeon map.
                if game_state.monster_locX > 0:
                    game_state.dungeon_map[game_state.monster_locX][game_state.monster_locY] = \
                        game_state.prev_monster
                game_state.prev_monster = game_state.active_monster
                game_state.monster_locX = viewx
                game_state.monster_locY = viewy
                message_update(screen, "A {} with {} points is near!".format(
                    game_state.monster_name, game_state.monster_hp))

                continue
    
    game_state.found_gold = gold_near


def monster_move(screen, game_state):
    pX, pY = game_state.player_locX, game_state.player_locY
    mX, mY = game_state.monster_locX, game_state.monster_locY
    dirX = 0; dirY = 0 

    if pX==mX and pY != mY:
        if pY < mY:
            dirY = -1
        elif pY > mY:
            dirY = 1
    elif pY==mY and pX != mX:
        if pX < mX:
            dirX = -1
        elif pX > mX:
            dirX = 1
    elif pX < mX and pY < mY:
        dirX = -1; dirY = -1
    elif pX < mX and pY > mY:
        dirX = -1; dirY = 1
    elif pX > mX and pY < mY:
        dirX = 1; dirY = -1
    elif pX > mX and pY > mY:
        dirX = 1; dirY = 1

    target = game_state.dungeon_map[mX+dirX][mY+dirY]
    
    # If we can't move into the target because there is something there that
    # we can't cross, then just stay put.
    if target == BLANK or target == BORDER or target==DOOR:
        game_state.player_map[mX][mY] = game_state.active_monster
        return

    game_state.player_map[mX][mY] = game_state.monster_whats_here
    mX+=dirX; mY+=dirY
    game_state.monster_whats_here = game_state.player_map[mX][mY]
    game_state.player_map[mX][mY]=game_state.active_monster
    game_state.monster_locX, game_state.monster_locY = mX, mY
    if mX==pX and mY==pY:
        attack(screen, game_state)


def attack(screen, game_state):
    message_update(screen, "AN ATTACK!", True)
    player_power = game_state.player_HP+game_state.player_experience
    monster_attack=random()*game_state.monster_hp/2+game_state.monster_hp/4
    player_attack=random()*player_power/2+player_power/4
    game_state.monster_hp=int(game_state.monster_hp-player_attack)
    game_state.player_HP=int(game_state.player_HP-monster_attack)

    # Is the PC dead? If not, continue with attack results
    if game_state.player_HP > 0:
        # If monster is twice as strong as player, it will make
        # an offer that the player can't refuse...
        if (game_state.monster_hp/game_state.player_HP+1)>2:
            message_update(screen, 
                "The {} will leave, IF you will give it half your gold.".format(
                game_state.monster_name))
            responded = False
            answer = ""
            while not responded:
                answer = get_input(screen, "Will you consent to this (Y or N)? ")
                if answer.startswith("y") or answer.startswith("n"):
                    responded = True
            if answer == "y":
                # Take the gold, the monster disappears!
                game_state.player_gold -= int(game_state.player_gold/2)
                remove_monster(game_state)
                return
        elif game_state.monster_hp > 0:
            message_update(screen, 
              "The {} has {} hit points".format(game_state.monster_name,
                                                game_state.monster_hp))
            return
        else:
            # The monster is dead
            game_state.player_experience += game_state.monster_level
            game_state.monsters_killed += 1
            message_update(screen, 
                           "The {} is dead!".format(game_state.monster_name))
            remove_monster(game_state)
            if game_state.player_experience >= game_state.next_level * 2:
                game_state.next_level = game_state.player_experience
                game_state.player_HP *= 3
                message_update(screen, "Your hit pts. have been raised")
                return
    else:
        # Death routine will be handled from check in main loop.
        return
    

def remove_monster(game_state):
    game_state.whats_here = FLOOR
    game_state.monster_locX = 0
    game_state.monster_locY = 0
    game_state.active_monster = ""
    game_state.monster_delay = 0
    game_state.monster_whats_here = FLOOR

    game_state.player_map[game_state.player_locX][game_state.player_locY] = PLAYER


def display_dungeon_map(screen, map, final=False):
    for row in range(0, HEIGHT):
        rowstr = ""
        for col in range(0,WIDTH):
            rowstr += map[col][row]
        screen.addstr(row+2, 0, rowstr)
        screen.refresh()
        if final:
            sleep(.5)

def end_game(screen, game_state, end_message):
    screen.clear()
    if end_message != "":
        message_update(screen, end_message)
        sleep(2)

    screen.addstr(STATUS_ROW, 0, "Gold: {} Exp: {} Killed {} Beasts".format(
        game_state.player_gold, 
        game_state.player_experience, 
        game_state.monsters_killed))

    screen.refresh()

def main(screen):
    # Display welcome
    display_welcome(screen)

    # Game loop
    while True:
        screen.clear()
        screen.addstr(STATUS_ROW, 0, "Setting up...")
        screen.refresh()

        # Ensure that our terminal/output device supports the screen size.
        num_rows, num_cols = screen.getmaxyx()
        assert num_rows >= HEIGHT and num_cols >= WIDTH, \
            "Terminal/screen needs to be {} rows by {} cols.".format(HEIGHT, WIDTH)

        # Initialize vars and maps
        # Look at annotated source and line 210 to see several of the variables needed
        # to be tracked through this game. Everything was global. To manage that mess,
        # I created a class struct to hold the game state.
        game = GameState()

        # Dungeon Map is the generated map
        game.dungeon_map = gen_dungeon()

        # Player Map is what is displayed to the player as they navigate the dungeon
        game.player_map = init_map()

        good_location = False
        while not good_location:
            game.player_locX = randint(1,WIDTH-1) 
            game.player_locY = randint(1,HEIGHT-1)
            good_location = \
                (game.dungeon_map[game.player_locX][game.player_locY]==FLOOR)

        # Determine/display what is visible
        what_is_seen(screen, game)

        game.player_map[game.player_locX][game.player_locY]=PLAYER
        game.whats_here = FLOOR

        # Input/Move loop
        playing = True
        while playing:
            map_move = False
            # Eligible moves are 1-9 for directions
            # except 5, which is a "wait" (and heal!)
            # S is 'see more' and q is quit.
            # so if 5 or S, update HP, continue to get input.
            # if q, then break out of this while and stop playing. 
            # if invalid input (""), continue to get input till valid.
            # Otherwise, continue on to calculate the results of the move!
            while not map_move:
                display_dungeon_map(screen, game.player_map)
                move = get_player_move(screen, game)

                if move == "":
                    pass

                elif move == "5":     # Rest/recover HP
                    game.player_HP += 1+sqrt(game.player_experience/game.player_HP)
                    map_move = True
                    move = 5

                elif move == "s":     # See more mode
                    game.see_more = True
                    game.player_HP -= 2
                    map_move = True   # Force a map move/screen refresh
                    move = 5          # but make it a "stay put" move.

                elif move == "q":     # Quit game
                    playing = False
                    break

                else:
                    map_move = True
                    move = int(move)

            # You lose HP as you move, doubly so if you are in shift
            # mode to move through walls. If we drop below 0XP, end of game.
            game.player_HP -= .15 + (2 * game.shift_mode)
            if game.player_HP <= 0:
                playing = False
                break

            # If we're here, we're moving. Check to see if we're moving
            # thru the spaces between rooms and not in in shift-move
            # mode. Then, check to see if we're trying to move through an 
            # impassable border. In either case, go get player input again.
            # Otherwise make the move.
            if map_move: 
                moveX,moveY = MOVEMAP[move]
                locX,locY = game.player_locX,game.player_locY
                if (game.dungeon_map[locX+moveX][locY+moveY]==BLANK \
                    and game.shift_mode!=1) or \
                    (game.dungeon_map[locX+moveX][locY+moveY]==BORDER):
                    continue
                else:
                    game.player_map[locX][locY]=game.whats_here
                    game.whats_here = game.dungeon_map[locX+moveX][locY+moveY]
                    game.player_map[locX+moveX][locY+moveY]=PLAYER
                    game.player_locX=locX+moveX
                    game.player_locY=locY+moveY

                    # What do we see now as a result of the move?
                    what_is_seen(screen, game)

                    # If we moved onto gold...
                    if game.whats_here == GOLD:
                        game.player_gold+=game.gold_stash
                        message_update(screen, "You found {} gold pieces!".format(game.gold_stash))
                        game.dungeon_map[game.player_locX][game.player_locY] = FLOOR
                        game.whats_here = FLOOR
                        game.hidden_gold -= 1
                        if game.hidden_gold == 0:
                            playing = False
                            break
                
                    # If we move onto a monster, attack!
                    if game.whats_here in MONSTERS:
                        attack(screen, game)

                        if game.player_HP <= 0:
                            playing = False
                            break

                    # If there's an active monster on the map,
                    # check its delay, if its delay is > 1, then
                    # it can move. This gives the player a chance
                    # to escape!
                    if game.monster_locX > 0:
                        game.monster_delay += 1
                    if game.monster_delay > 1:
                        monster_move(screen, game)
                        # There can be an attack after the monster
                        # move, so check player HP again.
                        if game.player_HP <= 0:
                            playing = False
                            break

        if game.player_HP <= 0:
            end_game(screen, game,"You're dead!")
        elif game.hidden_gold == 0:
            end_game(screen, game,"You found all the gold! You won!")
        else:
            end_game(screen, game, "")

        # Display the dungeon map
        display_dungeon_map(screen, game.dungeon_map, True)

        playagain = get_input(screen, "Want to play again? ")
        if not playagain.startswith("y"):
            sys.exit(0)

# Safely start/end curses windowing
curses.wrapper(main)
