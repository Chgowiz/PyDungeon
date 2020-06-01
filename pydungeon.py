# Recreation of DUNGEON, a game written by Brian Sawyer for Cursor Magazine,
# issue #15. Published in Dec 1979. 

from random import random, randint, choice
import sys
from os import system, name
from time import sleep
from math import sqrt

WIDTH = 40
HEIGHT = 25
RM_GEN_RETRIES = 50
DESIRED_RMS = 8
MONSTERS = ["R","G","D","S","N","W"]
FLOOR = "."
DOOR = "+"
GOLD = "g"
NUM_HIDDEN_GOLD = 11
BORDER = "*"
PLAYER = "@"
VALIDMOVES = "qs123456789"
MOVEMAP = [41,80,81,82,40,41,42,0,1,2]

def cls():
    if name == "nt":
        _ = system("cls")
    else:
        _ = system("clear")

def display_welcome():
    cls()
    print("          PyDungeon\n    A recreation of CURSOR #15 DUNGEON")
    print("Original (C)1979 by Brian Sawyer.\nPyDungeon is public domain.")
    print("-" * 40)
    print("Search for GOLD in the ancient ruins\n")
    print("Press RETURN to begin")
    input()

def init_map():
    # Create new map/screen data structure
    # Returns: list of [WIDTH][HEIGHT] elements
    map_struct = []
    for row in range(HEIGHT):
        map_struct.append([])
        for col in range(WIDTH):
            map_struct[row].append(" ")

    return map_struct


def POKE(memory, location, value):
    # This translates the concept of a contiguous memory space that 
    # you can write to into writing to the data structure I've created.
    # In the PET, both regular memory and screen memory was contiguous,
    # and when writing to screen memory, PET then translated that 
    # position XYZ to row/col position on the screen when displaying the
    # screen.
    # So, in a sense, my POKE (and PEEK), does that work.
    # I used the concept of POKE/PEEK to simplify converting the code. 
    # Plus... my first programs used POKE/PEEK, so this amuses me 
    # greatly!
    memory[(location//WIDTH)][(location%WIDTH)] = value


def PEEK(memory, location):
    # See comments above for POKE in how PEEK works. 
    return memory[(location//WIDTH)][(location%WIDTH)]


def gen_room_loc(RS, CS):
    W = int(random()*9+2); L = int(random()*9+2)
    R0=int(random()*(RS-L-1))+1; C0=int(random()*(CS-W-1))+1; P=40*R0+C0
    return W, L, R0, C0, P


def gen_dungeon(SZ, RS, CS):
    # We return a list data structure that represents a map of 40 columns, 
    # 25 rows. The dungeon is generated inside this structure and serves
    # to feed what will be seen on the screen. In a sense, we'll have two 
    # structures - the full map, and then the map that the player reveals 
    # and what gets painted to the screen.
    # See "dungeon-memory-sim.py" for my notes on how this all worked in the
    # original source, I've removed that from this code. 
    mem = []
    mem = init_map()

    retries = 0
    rooms_generated = 0
    # Keep generating rooms until we've hit a limit of DESIRED_RMS rooms or we've maxed out with 
    # retries of so many times (RM_GEN_RETRIES) . 
    while rooms_generated < DESIRED_RMS and retries < RM_GEN_RETRIES:
        W, L, R0, C0, P = gen_room_loc(RS, CS)

        # This was a check to see if the room in the data structure would go over
        # the boundaries (end point) of the area of memory allocated. (TS+SZ)
        if P+40*L+W >= SZ:
            fail_on_size += 1
            continue

        # This looks to see if the room overlaps other rooms.
        # I know the -1 looks strange, but the game should keep rooms at least 1
        # space apart. Since I'm 0 index and BASIC was 1 indexed, this is how 
        # it will work.
        failed_check = False
        for N in range(-1,(L+1)+1):
            for N1 in range(-1, (W+1)+1):
                if PEEK(mem, P+(N*40+N1)) != " ":
                    failed_check = True
                    break

            if failed_check:
                retries += 1
                break

        if not failed_check:
            # We have a good room!
            # This fills the room space.
            rooms_generated += 1
            for N in range(0,L+1):
                for N1 in range(0, W+1):
                    POKE(mem, P+(N*40+N1), FLOOR)

            # Generate vertical passages from generated room down.
            for N in range(P+42+(L*40), 999+1, 40):
                if PEEK(mem,N) == FLOOR:
                    for N1 in range(P+42, N+1, 40):
                        POKE(mem, N1, FLOOR)
                    # I think this used to be N1-80 because FOR NEXT in PET would increment, check
                    # and leave the value at the incremented, which meant you'd have to back up
                    # two rows. It seems that Python doesn't do that, so if I only back up 40, the
                    # door symbol (in memory map, remember) is in the right spot.
                    POKE(mem, N1-40, DOOR)
                    break

            # Generate horizontal passages from generated room right.
            start = P+81+W; end = P+121+W 
            for N in range(start, end+1):
                if N/40 == int(N/40):
                    break
                
                if PEEK(mem, N) == FLOOR:
                    for N1 in range(P+81, (N-1)+1):
                        POKE(mem, N1, FLOOR)
                    POKE(mem, N1, DOOR)
                    break

            # Generate a monster in the room. Every room has a monster!
            S = int(random()*L)+1; S1 = int(random()*W+1)
            POKE(mem, P+S1+S*40, choice(MONSTERS))

    # Distribute 11 gold around the dungeon
    for N in range(1, NUM_HIDDEN_GOLD+1):
        is_room = False
        while not is_room:
            U = int(random()*SZ)
            is_room = (PEEK(mem,U) == FLOOR)
        POKE(mem, U, GOLD)

    # Generate hard borders - player cannot cross these.
    for R0 in range(0,RS+1):
        POKE(mem, 40*R0, BORDER)
        POKE(mem, 40*R0+CS, BORDER)

    for C0 in range(0, CS+1):
        POKE(mem, C0, BORDER)
        POKE(mem, C0+40*RS, BORDER)

    return mem

def what_is_seen(dungeon_map, players_map, L, SM, MG, K1):

    ## BUG ## - the view "wraps" if we're right next to the border. The border needs
    # to stop the view

    if SM==1:
        K=80; J=-2; R=3; SM=0
    else:
        K=40; J=-1; R=2

    for N in range(K*-1, K+1, 40):    # col position - left, center, right
        for N1 in range(J,R):       # row position - above, center, below
            if N==0 and N1==0:      # if we're looking at our curr position...
                continue            # ... then ignore. We know what's here!
            Y=L+N+N1
            V=PEEK(dungeon_map, Y)
            POKE(players_map, Y, V)
            if V==DOOR or V==FLOOR or V==BORDER:
                continue
            if V==GOLD:
                K1=1+K1+int((MG+1)*(random()))  # We found gold! How much?
                                                # See notes on source ln 680
                continue
            if V in MONSTERS:
                continue
    #710 V1=V+128:S=0:POKEY+TS,160
    #720 IFV=86THENE$="SPIDER":I=3
    #730 IFV=87THENE$="GRUE":I=7
    #740 IFV=88THENE$="DRAGON":I=1
    #750 IFV=89THENE$="SNAKE":I=2
    #760 IFV=90THENE$="NUIBUS":I=9
    #770 IFV=91THENE$="WYVERN":I=5
    #780 I=INT(RND(1)*HP+(PX/I)+HP/4)
    #790 IFE>0THENPOKETS+E,QQ
    #800 QQ=V+128:E=Y
    #810 GOSUB1410:PRINT"A "E$;" WITH";I;"POINTS IS NEAR.":GOSUB1430:CC=I
    #820 NEXTN1:NEXTN:FG=GN:RETURN
    
    return K1, SM

def display_dungeon_map(map, final=False):
    cls()
    for row in map[:-2]:
        print("".join(row))
        if final:
            sleep(.5)

def get_player_input(HP, EX, MG):
    print("HIT PTS. {}  EXP. {}  GOLD {}".format(int(HP+.5), EX, MG))
    print("You may move. ", end="")

    move = input().lower().strip()
    if len(move) > 1 or move not in VALIDMOVES:
        move = ""
    return move


def end_game(MG, EX, Z, end_message):
    print(end_message)
    print("Gold: {} Exp: {} Killed {} Beasts".format(MG, EX, Z))
    input("Press return to see the dungeon map. ")

# Display welcome
display_welcome()

# Game loop
while True:
    # Initialize vars and maps
    cls()
    print("Setting up...")

    # RS/CS are row size, col size for display.
    # The other variables are used for screen painting purposes.
    # TS and AX are key variables in the game, they were used to mark the points 
    # where the program could generate an in-memory map (TS) and then AX was the
    # point where PET screen memory began. POKEing to locations at AX and beyond
    # would write to the screen!
    # We don't really need TS or AX in this program, so I've done away with them.
    RS=23; CS=40; SZ=RS*CS; BL=(25-RS)*40 ; RS=RS-1; CS=CS-1

    # Dungeon Map is the generated map
    dungeon_map = gen_dungeon(SZ, RS, CS)

    # Player Map is what is displayed to the player as they navigate the dungeon
    player_map = init_map()

    # 210 HP=50:MG=0:EX=0:PX=0:HG=0:Z=0:FG=0:K1=0:E=0:S=0:W=160:ET=160
    # HP is player hit points; MG is gold recovered; EX is experience earned
    # HG is hidden gold; Z is number of monsters killed; SX is "shift mode" to move
    # thru walls [not sure how I'm going to implement that yet...]; W is what was in
    # the space that the player just moved thru; K1 is how much gold has been uncovered; 
    # SM is "see mode" - look further. Not well or completely implemented by Brian.

    HP=50; MG=0; EX=0; HG=NUM_HIDDEN_GOLD; Z=0; SX=0; W=FLOOR; K1=0; 
    SM=0

    good_location = False
    while not good_location:
        L = int(random()*SZ)
        good_location = (PEEK(dungeon_map, L) == FLOOR)
    
    # 260 TM=0:GOSUB1410:L=L+AX-TS:W=PEEK(L):GOSUB600:POKEL,209:W=160
    W = PEEK(dungeon_map, L)

    # Determine/display what is visible
    K1, SM = what_is_seen(dungeon_map, player_map, L, SM, MG, K1)

    POKE(player_map, L, PLAYER)
    W = FLOOR

    # Input/Move loop
    # This is not set up like DUNGEON!
    # Since (right now), Python doesn't accept keystrokes and respond to them
    # immediately - it requires a return for input (I'm going to look into curses!)
    # So the input/play loop is a little different. 
    # I'm also not limiting input to 1 per second. 
    playing = True
    while playing:
        map_move = False
        # Eligible moves are 1-9 for directions
        # except 5, which is a "wait" (and heal!)
        # S which is --notsure-- and q which is quit.
        # so if 5 or S, update HP, continue to get input.
        # if q, then break out of this while and stop playing. 
        # if invalid input (""), continue to get input till valid.
        # Otherwise, continue on to calculate the results of the move
        while not map_move:
            display_dungeon_map(player_map)
            move = get_player_input(HP, EX, MG)

            if move == "":
                pass
            elif move == "5":     # Rest/recover HP
                HP += 1+sqrt(EX/HP)
                map_move = True
            elif move == "s":     # See more mode
                SM = 1; HP -= 2
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
        HP=HP-.15-2*SX 
        if HP < 0:
            playing = False
            break

        # If we're here, we're moving. Check to see if we're moving
        # thru the spaces between rooms - if so, we need to be in shift
        # mode. (not sure how I'm going to implement that.) Then, check
        # to see if we're trying to move through an impassable order.
        # In either case, go get player input again.
        # See annotated source for how Q works, but it essentially 
        # converts the player direction input into the number of 
        # grid spaces (assume 40c x 25r screen) to move the player.
        if map_move: 
            Q = MOVEMAP[move]-41
            if (PEEK(dungeon_map,L+Q)==" " and SX!=1) or \
                (PEEK(dungeon_map,L+Q)==BORDER):
                continue
            else:
                POKE(player_map,L,W)
                L=L+Q
                W = PEEK(dungeon_map,L)
                POKE(player_map,L,PLAYER)

                K1, SM = what_is_seen(dungeon_map, player_map, L, SM, MG, K1)

                if W == GOLD:
                    MG=MG+K1
                    print("You found {} gold pieces!".format(K1))
                    POKE(dungeon_map, L, FLOOR)
                    W = FLOOR
                    HG -= 1
                    if HG == 0:
                        playing = False
                        break

    if HP <= 0:
        end_game(MG,EX,Z,"You're dead!")
    if HG == 0:
        end_game(MG,EX,Z,"You found all the gold! You won!")

    # Display the dungeon map
    display_dungeon_map(dungeon_map, True)

    print("Want to play again? ", end="")
    if not input().lower().startswith("y"):
        sys.exit(0)