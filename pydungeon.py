# Recreation of DUNGEON, a game written by Brian Sawyer for Cursor Magazine,
# issue #15. Published in Dec 1979. 
# Michael Shorten, June 2020, Public Domain, I have no rights to original
# source. I am doing this for educational purposes to demonstrate computer
# history and what it might look like in modern programming.

from random import random, randint, choice
import sys
from os import system, name
from time import sleep
from math import sqrt

WIDTH = 40
HEIGHT = 25
RM_GEN_RETRIES = 50
DESIRED_RMS = 8
MONSTERS = ["X","G","D","S","N","W"]
FLOOR = "."
DOOR = "+"
GOLD = "g"
NUM_HIDDEN_GOLD = 11
BORDER = "*"
PLAYER = "@"
VALIDMOVES = "qs123456789"
MOVEMAP = [41,80,81,82,40,41,42,0,1,2]
PRINT_PAUSE = 1

class GameState():

    def __init__(self):
        # RS/CS are row size, col size for display.
        # The other variables are used for screen painting purposes.
        # TS and AX are key variables in the game, they were used to mark the points 
        # where the program could generate an in-memory map (TS) and then AX was the
        # point where PET screen memory began. POKEing to locations at AX and beyond
        # would write to the screen!
        # We don't really need TS or AX in this program, so I've done away with them.
        self.RS=23; self.CS=40
        self.SZ=self.RS*self.CS
        self.BL=(25-self.RS)*40
        self.RS-=1; self.CS-=1

        self.dungeon_map = []
        self.player_map = []

        self.hidden_gold = NUM_HIDDEN_GOLD
        self.gold_stash = 0
        self.found_gold = False

        self.whats_here = FLOOR
        self.see_more = False
        self.shift_mode = 0

        self.player_loc = 0
        self.player_HP = 50
        self.player_gold = 0
        self.player_experience = 0
        self.monsters_killed = 0
        self.next_level = 0

        self.active_monster = ""
        self.monster_name = ""
        self.monster_level = 0
        self.monster_hp = 0
        self.monster_loc = 0
        self.monster_S = 0
        self.prev_monster = ""


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
    print_pause("Search for GOLD in the ancient ruins\n")
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


def what_is_seen(game_state):

    ## BUG ## - the view "wraps" if we're right next to the border. The border needs
    # to stop the view
    
    gold_near = False

    if game_state.see_more:
        K=80; J=-2; R=3; game_state.see_more = False
    else:
        K=40; J=-1; R=2

    for N in range(K*-1, K+1, 40):    # col position - left, center, right
        for N1 in range(J,R):       # row position - above, center, below
            if N==0 and N1==0:      # if we're looking at our curr position...
                continue            # ... then ignore. We know what's here!
            Y=game_state.player_loc+N+N1
            V=PEEK(game_state.dungeon_map, Y)
            POKE(game_state.player_map, Y, V)

            if V==DOOR or V==FLOOR or V==BORDER:
                continue
            if V==GOLD:
                # We found gold! How much?
                # See notes on source ln 680
                game_state.gold_stash += 1+int(
                    (game_state.player_gold+1)*(random()))  
                gold_near = True
                # If we've not been near this gold, announce it.
                if not game_state.found_gold:
                    print_pause("Gold is near!")
                
                continue
            if V in MONSTERS:
                if V=="X":
                    game_state.monster_name="Spider"
                    game_state.monster_level=3
                elif V=="G":
                    game_state.monster_name="Grue"
                    game_state.monster_level=7
                elif V=="D":
                    game_state.monster_name="Dragon"
                    game_state.monster_level=1
                elif V=="S":
                    game_state.monster_name="Snake"
                    game_state.monster_level=2
                elif V=="N":
                    game_state.monster_name="Nuibus"
                    game_state.monster_level=9
                elif V=="W":
                    game_state.monster_name="Wyvern"
                    game_state.monster_level=5

                game_state.active_monster = V
                
                ## TODO - uncomment this when we want to have the active
                # monster move.
                # POKE(game_state.dungeon_map, Y, FLOOR)

                game_state.monster_S = 0

                # Monster HP based on our HP, experience and random
                # We save the level for later if we defeat the monster, to 
                # get XP from!
                # It will change each time we see this monster. Heh.
                game_state.monster_hp = game_state.monster_level = \
                    int(random()*game_state.player_HP + 
                     (game_state.player_experience/game_state.monster_level) + 
                     game_state.player_HP/4)

                # If we've already revealed a monster, put it back on the
                # dungeon map.
                if game_state.monster_loc > 0:
                    POKE(game_state.dungeon_map, game_state.monster_loc, 
                         game_state.prev_monster)
                game_state.prev_monster = game_state.active_monster
                game_state.monster_loc = Y
                print_pause("A {} with {} points is near!".format(
                    game_state.monster_name, game_state.monster_hp))

                continue
    
    game_state.found_gold = gold_near

def attack(game_state):
    print_pause("## AN ATTACK! ##")
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
            print_pause("The {} will leave, IF you will give it half your gold.".format(
                game_state.monster_name))
            responded = False
            answer = ""
            while not responded:
                answer = input("Will you consent to this (Y or N)? ").lower().strip()
                if answer.startswith("y") or answer.startswith("n"):
                    responded = True
            if answer == "y":
                # Take the gold, the monster disappears!
                game_state.player_gold -= int(game_state.player_gold/2)
                remove_monster(game_state)
                return
        elif game_state.monster_hp > 0:
            print_pause("The {} has {} hit points".format(game_state.monster_name,
                                                    game_state.monster_hp))
            return
        else:
            # The monster is dead
            game_state.player_experience += game_state.monster_level
            game_state.monsters_killed += 1
            print_pause("The {} is dead!".format(game_state.monster_name))
            remove_monster(game_state)
            if game_state.player_experience >= game_state.next_level * 2:
                game_state.next_level = game_state.player_experience
                game_state.player_HP *= 3
                print_pause("Your hit pts. have been raised")
                return
    else:
        # Death routine will be handled from check in main loop.
        return
    

def remove_monster(game_state):
    game_state.whats_here = FLOOR
    game_state.monster_loc = 0
    game_state.active_monster = ""
    game_state.monster_S = 0
    POKE(game_state.player_map, game_state.player_loc, PLAYER)


def print_pause(msg):
    print(msg)
    sleep(PRINT_PAUSE)


def display_dungeon_map(map, final=False):
    cls()
    for row in map[:-2]:
        print("".join(row))
        if final:
            sleep(.5)


def get_player_input(game_state):
    print("HIT PTS. {}  EXP. {}  GOLD {}".format(
        int(game_state.player_HP+.5), 
        game_state.player_experience, 
        game_state.player_gold))
    print("You may move. ", end="")

    move = input().lower().strip()
    if len(move) > 1 or move not in VALIDMOVES:
        move = ""
    return move


def end_game(game_state, end_message):
    print_pause(end_message)
    print("Gold: {} Exp: {} Killed {} Beasts".format(
        game_state.player_gold, 
        game_state.player_experience, 
        game_state.monsters_killed))
    input("Press return to see the dungeon map. ")


# Display welcome
display_welcome()

# Game loop
while True:
    # Initialize vars and maps
    cls()
    print("Setting up...")

    # Look at annotated source and line 210 to see several of the variables needed
    # to be tracked through this game. Everything was global. To manage that mess,
    # I created a class struct to hold the game state.
    game = GameState()

    # Dungeon Map is the generated map
    game.dungeon_map = gen_dungeon(game.SZ, game.RS, game.CS)

    # Player Map is what is displayed to the player as they navigate the dungeon
    game.player_map = init_map()

    good_location = False
    while not good_location:
        game.player_loc = int(random()*game.SZ)
        good_location = (PEEK(game.dungeon_map, game.player_loc) == FLOOR)
    
    game.whats_here = PEEK(game.dungeon_map, game.player_loc)

    # Determine/display what is visible
    what_is_seen(game)

    POKE(game.player_map, game.player_loc, PLAYER)
    game.whats_here = FLOOR

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
        # S is 'see more' and q is quit.
        # so if 5 or S, update HP, continue to get input.
        # if q, then break out of this while and stop playing. 
        # if invalid input (""), continue to get input till valid.
        # Otherwise, continue on to calculate the results of the move!
        while not map_move:
            display_dungeon_map(game.player_map)
            move = get_player_input(game)

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
        game.player_HP -= .15 - 2 * game.shift_mode
        if game.player_HP <= 0:
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
            if (PEEK(game.dungeon_map,game.player_loc+Q)==" " \
                and game.shift_mode!=1) or \
                (PEEK(game.dungeon_map,game.player_loc+Q)==BORDER):
                continue
            else:
                POKE(game.player_map,game.player_loc,game.whats_here)
                game.player_loc+=Q
                game.whats_here = PEEK(game.dungeon_map,game.player_loc)
                POKE(game.player_map,game.player_loc,PLAYER)

                # What do we see now as a result of the move?
                #CC,E,S,V1,ESTR = what_is_seen()
                what_is_seen(game)

                # If we moved onto gold...
                if game.whats_here == GOLD:
                    game.player_gold+=game.gold_stash
                    print_pause("You found {} gold pieces!".format(game.gold_stash))
                    POKE(game.dungeon_map, game.player_loc, FLOOR)
                    game.whats_here = FLOOR
                    game.hidden_gold -= 1
                    if game.hidden_gold == 0:
                        playing = False
                        break
                
                # If we move onto a monster, attack!
                if game.whats_here in MONSTERS:
                    attack(game)

                    if game.player_HP <= 0:
                        playing = False
                        break

                # If there's an active monster, it moves, and
                # can attack, same "round"


    if game.player_HP <= 0:
        end_game(game,"You're dead!")
    if game.hidden_gold == 0:
        end_game(game,"You found all the gold! You won!")

    # Display the dungeon map
    display_dungeon_map(game.dungeon_map, True)

    print("Want to play again? ", end="")
    if not input().lower().startswith("y"):
        sys.exit(0)