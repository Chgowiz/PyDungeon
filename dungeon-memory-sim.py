# Simulating what goes on in the memory structure
# of DUNGEON

import random
import sys
from os import system, name

WIDTH = 40
HEIGHT = 25
RM_GEN_RETRIES = 50
DESIRED_RMS = 8
ASCII_a = ord('a')
t_vars = {}

def draw_memory(data, vars_dict, step=""):
    cls()
    # Draw the board data structure
    margin = "    "
    tens_line = margin + " "      # Initial space for left side of board
    for i in range(1,(WIDTH//10)):
        tens_line += (" " * 9) + str(i)
    digits_line = margin + ("0123456789" * (WIDTH//10))
    if step != "":
        print("=== {} ===".format(step))
    print(tens_line)
    print(digits_line)

    for row in range(HEIGHT):
        # single digit numbers are padded with extra space
        if row < 10:
            extra_space = " "
        else:
            extra_space = ""

        print("{}{}| ".format(extra_space, row), end="")
        for col in range(WIDTH):
            print(data[row][col], end="")
        print(" |{}{}".format(extra_space,row))
    print(digits_line)
    print(tens_line)
    get_continue(vars_dict)


def init_memory():
    # Create new data structure
    # Returns: list of [WIDTH][HEIGHT] elements
    board = []
    for row in range(HEIGHT):
        board.append([])
        for col in range(WIDTH):
            board[row].append("~")

    return board


def get_continue(vars_dict):
    var_str = ""
    for k,v in vars_dict.items():
        var_str += "{}={}, ".format(k,v)
    print(var_str)
    input("Press return to continue...")


def POKE(memory, location, value):
    memory[(location//WIDTH)][(location%WIDTH)] = value


def PEEK(memory, location):
    return memory[(location//WIDTH)][(location%WIDTH)]


def cls():
    if name == "nt":
        _ = system("cls")
    else:
        _ = system("clear")


def gen_room_loc(TS):
    W = int(random.random()*9+2); L = int(random.random()*9+2)
    R0=int(random.random()*(RS-L-1))+1; C0=int(random.random()*(CS-W-1))+1; P=TS+40*R0+C0
    return W, L, R0, C0, P


def gen_dungeon(TS, SZ):
    # We return a map of 40x25 (x,y)
    mem = []
    mem = init_memory()

    # 200 FOR I= TS + 40 TO TS + SZ-41:POKEI,32:NEXTI
    for i in range(TS+40, (TS+SZ-41)+1):
        # POKE treats this as a continuous area of data, not divided
        # into an x,y list like we have here. So, create a function POKEds that will
        # take a number, and then map to our row/col coordinate system
        # Also, BASIC FOR is inclusive of start, stop, so we have to add 1
        # because Python for is exclusive of stop
        POKE(mem, i, " ")
        # t_vars["i"] = i

    # draw_memory(mem, t_vars, "INIT")

    retries = 0
    rooms_generated = 0
    # Keep generating rooms until we've hit a limit of 8 rooms or we've maxed out with 
    # retries of so many times (RM_GEN_RETRIES) . 
    while rooms_generated < DESIRED_RMS and retries < RM_GEN_RETRIES:
        W, L, R0, C0, P = gen_room_loc(TS)

        # 400 W=INT(RND(1)*9+2):L=INT(RND(1)*9+2)
        # 410 R0=INT(RND(1)*(RS-L-1))+1:C0=INT(RND(1)*(CS-W-1))+1:P=TS+40*R0+C0
        # 420 IFP+40*L+W>=TS+SZTHEN530

        # This was a check to see if the room in the data structure would go over
        # the boundaries (end point) of the area of memory allocated. (TS+SZ)
        if P+40*L+W >= TS+SZ:
            fail_on_size += 1
            continue

        # t_vars["W"] = W; t_vars["L"] = L
        # t_vars["R0"] = R0; t_vars["C0"] = C0; t_vars["P"] = P

        #430 FORN=0TOL+1:FORN1=0TOW+1:IFPEEK(P+(N*40)+N1)<>32THEN530
        #440 NEXTN1,N
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
            #450 FORN=1TOL:FORN1=1TOW:POKEP+(N*40)+N1,160:NEXTN1,N
            # We have a good room!
            # This fills the room space. For now, I'll use # to denote room space.
            rooms_generated += 1
            for N in range(0,L+1):
                for N1 in range(0, W+1):
                    POKE(mem, P+(N*40+N1), "#")

    return mem

# Simulating the values from Dungeon
# 100 RS=23: CS=40: SZ=RS*CS: BL=(25-RS)*40:RS=RS-1:CS=CS-1
# SZ = 920 - the number of spaces in a 23*40 data space
RS=23; CS=40; SZ=RS*CS; BL=(25-RS)*40 ; RS=RS-1; CS=CS-1

t_vars["RS"] = RS
t_vars["CS"] = CS
t_vars["SZ"] = SZ
t_vars["BL"] = BL

# 190 TS=PEEK(QM)+256*PEEK(QM+1)-SZ:AX=32768
TS = 0      # In PET/Dungeon, this is 31848
            # but it doesn't matter here. 
            # We'll assume the starting point is 0

AX = TS + 920     # Since TS and AX start off at the same point, 
                # and then TS is backed off by 920, we'll reverse
                # that for now. 

# In PETs, 32768 was start of screen RAM! POKEing to this location put 
# something at 0,0!

t_vars["TS"] = TS
t_vars["AX"] = AX

# 210 HP=50:MG=0:EX=0:PX=0:HG=0:Z=0:FG=0:K1=0:E=0:S=0:W=160:ET=160

# For giggles/grins, generate a whole bunch of maps
for dngmap in range(1,11):
    dungeon_map = gen_dungeon(TS, SZ)
    draw_memory(dungeon_map, t_vars, "MAP #{} GENERATED".format(dngmap))

