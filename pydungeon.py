# Recreation of DUNGEON, a game written by Brian Sawyer for Cursor Magazine,
# issue #15. Published in Dec 1979. 

from random import random, randint, choice
import sys
from os import system, name
from time import sleep

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

def cls():
    if name == "nt":
        _ = system("cls")
    else:
        _ = system("clear")

def display_welcome():
    cls()
    print("    PyDungeon\n    A recreation of CURSOR #15 DUNGEON")
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
            map_struct[row].append("~")

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


def gen_room_loc(TS):
    W = int(random()*9+2); L = int(random()*9+2)
    R0=int(random()*(RS-L-1))+1; C0=int(random()*(CS-W-1))+1; P=TS+40*R0+C0
    return W, L, R0, C0, P


def gen_dungeon(TS, SZ):
    # We return a list data structure that represents a map of 40 columns, 
    # 25 rows. The dungeon is generated inside this structure and serves
    # to feed what will be seen on the screen. In a sense, we'll have two 
    # structures - the full map, and then the map that the player reveals 
    # and what gets painted to the screen.
    # See "dungeon-memory-sim.py" for my notes on how this all worked in the
    # original source, I've removed that from this code. 
    mem = []
    mem = init_map()

    for i in range(TS+40, (TS+SZ-41)+1):
        POKE(mem, i, " ")

    retries = 0
    rooms_generated = 0
    # Keep generating rooms until we've hit a limit of DESIRED_RMS rooms or we've maxed out with 
    # retries of so many times (RM_GEN_RETRIES) . 
    while rooms_generated < DESIRED_RMS and retries < RM_GEN_RETRIES:
        W, L, R0, C0, P = gen_room_loc(TS)

        # This was a check to see if the room in the data structure would go over
        # the boundaries (end point) of the area of memory allocated. (TS+SZ)
        if P+40*L+W >= TS+SZ:
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
            for N in range(P+42+(L*40), TS+999+1, 40):
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
                if (N-TS)/40 == int((N-TS)/40):
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
            U = int(random()*SZ)+TS
            is_room = (PEEK(mem,U) == FLOOR)
        POKE(mem, U, GOLD)

    # Generate hard borders - player cannot cross these.
    for R0 in range(0,RS+1):
        POKE(mem, TS+40*R0, BORDER)
        POKE(mem, TS+40*R0+CS, BORDER)

    for C0 in range(0, CS+1):
        POKE(mem, TS+C0, BORDER)
        POKE(mem, TS+C0+40*RS, BORDER)

    return mem

def display_dungeon_map(map):
    for row in map[:-2]:
        print("".join(row))
        sleep(.5)

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
    # We're setting TS to 0 here, since it really doesn't matter what the 'memory
    # location' is. In the original code, TS was AX - 920 (row*col = 920). 
    # We'll set AX to TS + 920.
    RS=23; CS=40; SZ=RS*CS; BL=(25-RS)*40 ; RS=RS-1; CS=CS-1
    TS = 0
    AX = TS + 920

    # Dungeon Map is the generated map
    dungeon_map = gen_dungeon(TS, SZ)

    # Player Map is what is displayed to the player as they navigate the dungeon
    player_map = init_map()

    # HP is player hit points; MG is gold recovered; EX is experience earned
    # HG is hidden gold
    HP=50; MG=0; EX=0; HG=NUM_HIDDEN_GOLD

    # Display the dungeon map
    display_dungeon_map(dungeon_map)

    print("Want to play again?")
    if not input().lower().startswith("y"):
        sys.exit(0)