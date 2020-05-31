# Simulating what goes on in the memory structure
# of DUNGEON

from random import random, randint, choice
import sys
from os import system, name

WIDTH = 40
HEIGHT = 25
RM_GEN_RETRIES = 50
DESIRED_RMS = 8
ASCII_a = ord("a")
t_vars = {}
MONSTERS = ["R","G","D","S","N","W"]
FLOOR = "."
DOOR = "+"
GOLD = "g"
BORDER = "*"
RS=23; CS=40; SZ=RS*CS; BL=(25-RS)*40 ; RS=RS-1; CS=CS-1

def draw_memory(data, vars_dict, step=""):
    cls()     # Works only if run from true terminal, not from IDE

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
    W = int(random()*9+2); L = int(random()*9+2)
    R0=int(random()*(RS-L-1))+1; C0=int(random()*(CS-W-1))+1; P=TS+40*R0+C0
    return W, L, R0, C0, P


def gen_dungeon(TS, SZ):
    # We return a list data structure that represents a map of 40 columns, 
    # 25 rows. The dungeon is generated inside this structure and serves
    # to feed what will be seen on the screen. In a sense, we'll have two 
    # structures - the full map, and then the map that the player reveals 
    # and what gets painted to the screen.
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
    # Keep generating rooms until we've hit a limit of DESIRED_RMS rooms or we've maxed out with 
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
                    POKE(mem, P+(N*40+N1), FLOOR)

            # Generate vertical passages from generated room down.
            # 460 FOR N=P+42+(L*40) TO TS+999 STEP 40
            # 470 IFPEEK(N)=160 THEN FOR N1=P+42 TO N STEP 40:POKE N1,160 : NEXT: POKEN1-80,102: GOTO490
            # 480 NEXT N
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

            # draw_memory(mem, t_vars, "END VPASS GEN")

            # Generate horizontal passages from generated room right.
            # 490 FOR N= P+81+W TO P+121+W:IF(N-TS)/40=INT((N-TS)/40)THEN520
            # N = 32303 + 81 + 6 (32390) TO 32303 + 121 + 6(32430)
            # IF (32390-31848)/40 = INT((32390-31848)/40) then no more passage/break;
            # 500 IFPEEK(N)=160THENFORN1=P+81TON-1:POKEN1,160:NEXT:POKEN1-1,102:GOTO520
            # 510 NEXT
            start = P+81+W; end = P+121+W 
            for N in range(start, end+1):
                if (N-TS)/40 == int((N-TS)/40):
                    break
                
                if PEEK(mem, N) == FLOOR:
                    for N1 in range(P+81, (N-1)+1):
                        POKE(mem, N1, FLOOR)
                    POKE(mem, N1, DOOR)
                    break

            # draw_memory(mem, t_vars, "END HPASS GEN")
            # Generate a monster in the room. Every room has a monster!
            # 520 S=INT(RND(1)*L)+1:S1=INT(RND(1)*W+1):POKEP+S1+S*40,INT(RND(1)*6+214)
            S = int(random()*L)+1; S1 = int(random()*W+1)
            POKE(mem, P+S1+S*40, choice(MONSTERS))

    # Distribute 11 gold around the dungeon
    # 540 FORN=1TO11
    # 550 U=INT(RND(1)*SZ)+TS:IFPEEK(U)<>160THEN550
    # 560 POKEU,135:HG=HG+1:NEXT
    for N in range(0,11):
        is_room = False
        while not is_room:
            U = int(random()*SZ)+TS
            is_room = (PEEK(mem,U) == FLOOR)
        POKE(mem, U, GOLD)
        # HG +=1

    # Generate borders (I think)
    # 570 FORR0=0TORS:POKETS+40*R0,127:POKETS+40*R0+CS,127:NEXTR0
    # 580 FORC0=0TOCS:POKETS+C0,127:POKETS+C0+40*RS,127:NEXTC0
    for R0 in range(0,RS+1):
        POKE(mem, TS+40*R0, BORDER)
        POKE(mem, TS+40*R0+CS, BORDER)

    for C0 in range(0, CS+1):
        POKE(mem, TS+C0, BORDER)
        POKE(mem, TS+C0+40*RS, BORDER)

    return mem

# Simulating the values from Dungeon
# 100 RS=23: CS=40: SZ=RS*CS: BL=(25-RS)*40:RS=RS-1:CS=CS-1
# SZ = 920 - the number of spaces in a 23*40 data space


#t_vars["RS"] = RS
#t_vars["CS"] = CS
#t_vars["SZ"] = SZ
#t_vars["BL"] = BL

# 190 TS=PEEK(QM)+256*PEEK(QM+1)-SZ:AX=32768
TS = 0      # In PET/Dungeon, this is 31848
            # but it doesn't matter here. 
            # We'll assume the starting point is 0

AX = TS + 920     # Since TS and AX start off at the same point, 
                # and then TS is backed off by 920, we'll reverse
                # that for now. 

# In PETs, 32768 was start of screen RAM! POKEing to this location put 
# something at 0 row, 0 col on the screen!

# t_vars["TS"] = TS
# t_vars["AX"] = AX

# 210 HP=50:MG=0:EX=0:PX=0:HG=0:Z=0:FG=0:K1=0:E=0:S=0:W=160:ET=160

# For giggles/grins, generate a whole bunch of maps
for dngmap in range(1,11):
    dungeon_map = gen_dungeon(TS, SZ)
    draw_memory(dungeon_map, t_vars, "MAP #{} GENERATED".format(dngmap))

