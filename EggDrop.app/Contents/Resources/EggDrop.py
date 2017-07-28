#!bin/python3.4
import pygame
import os, sys, threading
import random, time, json
from pygame.locals import *
from helper import *
from sprites import *

# Global Variables
SCREEN_HEIGHT = 700
SCREEN_WIDTH = 1000
FULLSCREEN = False

##############################
# Multiplayer mode Variables #
##############################
UDP_CLIENT = None # A socket indicating 'the' first connected client.
OPP = {'XPOS': [], 'HP': 10, 'SCORE': 0, 'CHICK_ID': -1}
PLAYER = {'XPOS':-1, 'HP':10, 'SCORE': 0, 'CHICK_ID': -1}
SEEDS = [] # List of available seeds
CONNECTED = False
SERVER = None # Only used in multiplayer hosting mode
SERVER_TIMEOUT = 0
CLIENT_TIMEOUT = False
'''
    STOP_GAME
    For client: Used by the loop to tell the client to stop sending data
    For server: Used by the server to tells the main loop to stop looping
'''
STOP_GAME = False

''' Encode an integer (0-2048) to 2 consecutive bytes'''
def data_encode(pos):
    pos = int(pos)
    return [pos >> 8, pos & 255]

''' Decode 2 consecutive bytes into an integer (0-2048)'''
def data_decode(pos):
    return (pos[0] << 8) + pos[1]

''' Worker function for threading purposes '''
def init_client(ip, port):
    UDPClient(ip, port)

''' Sending data to a specified server as a client '''
class UDPClient():
    def __init__(self, ip, port):
        global CONNECTED, STOP_GAME, CLIENT_TIMEOUT
        self.ip, self.port = ip, port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(2)
        start = True
        while 1:
            if not self.send(start=start):
                break
            if STOP_GAME:
                self.send(end=True)
                break
            CONNECTED = True
            time.sleep(0.02)
            if start:
                start = False
        self.sock.close()
        CONNECTED = False # Connection ended
        CLIENT_TIMEOUT = True

    def send(self, start=False, end=False):
        # Declare global variables
        global SEEDS, STOP_GAME, PLAYER, OPP
        '''
        Packet format (In): // Excluding Header
            2 random seeds: 2 bytes [0-255]
            Opponent x-pos: 2 bytes
            Opponent HP: 1 byte
            Opponent score: 2 bytes
        Packet format (Out): // Excluding Header
            Player x-pos: 2 bytes
            Player HP: 1 byte
            Player score: 2 bytes
        '''
        packet = []
        if start:
            packet += [2, PLAYER['CHICK_ID']] # 2 signifies start
        elif end:
            packet.append(1) # 1 signifies the server to stop
        else:
            packet = data_encode(PLAYER['XPOS'])
            packet.append(PLAYER['HP'])
            packet += data_encode(PLAYER['SCORE'])
        for i in range(5): # Send 10 packets and expect to get at least one response
            # Send data to the server
            self.sock.sendto(bytes(packet),
                            (self.ip, self.port))
            # Receive data from the server
            try:
                if start:
                    recv = self.sock.recv(1)
                    OPP['CHICK_ID'] = recv[0]
                elif end:
                    recv = self.sock.recv(1) # Make sure the server gets this request
                else:
                    recv = self.sock.recv(7)
                    # Write opponent data
                    SEEDS.append((recv[0], recv[1]))
                    OPP['XPOS'].append(data_decode([recv[2], recv[3]]))
                    OPP['HP'] = recv[4]
                    OPP['SCORE'] = data_decode([recv[5], recv[6]])
                return True # Successful send
            except socket.timeout: # Packet lost or extremely slow connection
                continue
        return False # Unsuccessful send

''' Handler for udp_host '''
class UDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Declare global variables
        global UDP_CLIENT, CONNECTED, SEEDS, PLAYER, OPP, STOP_GAME, SERVER_TIMEOUT
        SERVER_TIMEOUT = 0
        if len(self.request[0]) < 5:
            if self.request[0][0] == 0: # Clients says Hi
                self.request[1].sendto(bytes([0]), self.client_address)
            if self.request[0][0] == 1: # Client requests End of Game
                self.request[1].sendto(bytes([1]), self.client_address)
                STOP_GAME = True
            if self.request[0][0] == 2: # Client sends chick id
                self.request[1].sendto(bytes([PLAYER['CHICK_ID']]), self.client_address)
                OPP['CHICK_ID'] = self.request[0][1]
                UDP_CLIENT = self.client_address
                CONNECTED = True
            return

        if self.client_address == UDP_CLIENT: # Only listen to this client
            '''
            Packet format (In): // Excluding Header
                Opponent x-pos: 2 bytes
                Opponent HP: 1 byte
                Opponent score: 2 bytes
            Packet format (Out): // Excluding Header
                2 random seeds: 2 bytes [0-255]
                Player x-pos: 2 bytes
                Player HP: 1 byte
                Player score: 2 bytes
            '''
            # Grab/Generate data to send back
            seeds = [random.randint(0,255), random.randint(0,255)]
            player_xpos = data_encode(PLAYER['XPOS'])
            player_score = data_encode(PLAYER['SCORE'])
            # Send data
            packet = seeds + player_xpos + [PLAYER['HP']] + player_score
            self.request[1].sendto(bytes(packet), self.client_address)
            # Store opponent data and seeds in queues
            SEEDS.append((seeds[0], seeds[1]))
            data = self.request[0]
            opponent_xpos = data_decode(data[0:2])
            OPP['XPOS'].append(opponent_xpos)
            OPP['HP'] = data[2]
            OPP['SCORE'] = data_decode(data[3:5])


''' Initialize a UDP server '''
def udp_host(ip, port):
    global SERVER
    SERVER = socketserver.UDPServer((ip, port), UDPHandler)
    SERVER.serve_forever()

'''
Handles the main initialization of the game
'''
class Game:
    def close_server(self):
        global SERVER, CONNECTED
        CONNECTED = False
        SERVER.shutdown()
        SERVER.server_close()
        SERVER = None

    def restore_global_var(self, server=True): # Restore the values of all multiplayer variables
        global UDP_CLIENT, OPP, PLAYER, SEEDS, CONNECTED, SERVER, STOP_GAME
        global CLIENT_TIMEOUT, SERVER_TIMEOUT
        ##############################
        # Multiplayer mode Variables #
        ##############################
        UDP_CLIENT = None # A socket indicating 'the' first connected client.
        OPP = {'XPOS': [], 'HP': 10, 'SCORE': 0, 'CHICK_ID': -1}
        PLAYER = {'XPOS':-1, 'HP':10, 'SCORE': 0, 'CHICK_ID': -1}
        SEEDS = [] # List of available seeds
        CONNECTED = False
        if server:
            SERVER = None # Only used in multiplayer hosting mode
        STOP_GAME = False
        CLIENT_TIMEOUT = False
        SERVER_TIMEOUT = 0

    def load_userdata(self, username):
        fname = os.path.join('data', 'user_data.json')
        self.user_data_f = open(fname, 'r+')
        self.user_data = json.load(self.user_data_f)
        if username not in self.user_data:
            self.user_data[username] = {
                "volume": True,
                "highscore": [],
                "screen_width": SCREEN_WIDTH,
                "screen_height": SCREEN_HEIGHT}
        self.username = username

    def game_sprite_init(self):
        # Initialize chicken
        self.chicken = Chicken()
        # Initialize scorepad
        self.scorepad = Scorepad()
        # Initialize hp
        self.hp = HPBar()
        # Initialize lost screen
        self.lost_screen = LostScreen()
        # Pause icon
        self.pause = Pause()
        #####################
        # Main Game Objects #
        #####################
        # Initialize eggs (gold)
        self.egg_sprites = pygame.sprite.Group()
        # Initialize rock eggs
        self.stone_egg_sprites = pygame.sprite.Group()
        # Initialize chick babies
        self.chick_baby_sprites = pygame.sprite.Group()

    def multiplayer_main_sprite_init(self):
        self.multiconfig_screen = MultiConfigScreen(self.sounds['button'])
        self.connecting_screen = ConnectingScreen()

    def multiplayer_game_sprite_init(self):
        self.opp_chicken = Chicken(opp=True) # Initialize opponent chicken
        self.opp_hp = HPBar()
        self.opp_scorepad = Scorepad()

    def start_sprite_init(self):
        # Initialize backdrop
        self.backdrop = Backdrop()
        # Initialize volumn button
        self.volumn_button = VolumnButton()
        # Initialize start screen
        self.start_screen = StartScreen(self.sounds['button'], self.sounds['troll'])

    def sound_init(self):
        # Initialize sound
        self.sounds = {'background': load_music('background.ogg'),
                    'egg_get': load_music('egg_get.ogg'),
                    'egg_break': load_music('egg_break.ogg'),
                    'lost': load_music('lost.ogg'),
                    'chickbaby':load_music('chickbaby.ogg'),
                    'button':load_music('button.ogg'),
                    'troll': load_music('troll.ogg')}
        # Play background music continuously
        self.sounds['background'].play(-1)

    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
        # Initialize pygame
        pygame.init()
        self.width = width
        self.height = height
        if FULLSCREEN:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption('Egg Drop')
        # Set icon
        icn = load_image('icon_64.png')[0]
        pygame.display.set_icon(icn)
        #Initialize background and sprites
        self.sound_init()
        self.start_sprite_init()
        self.user_data_f = None
        self.user_data = None
        self.username = None
        self.clock = pygame.time.Clock()
        self.loop()

    def loop(self):
        global SCREEN_WIDTH, SCREEN_HEIGHT, SEEDS, SERVER_TIMEOUT
        global CONNECTED, SERVER, PLAYER, OPP, STOP_GAME, CLIENT_TIMEOUT
        obj_creation = 0 # Controls object creation during the gameplay
        current_screen = 'start_screen'
        status = 0
        played_lost_sound = False
        pause = False
        multiplayer = False
        while 1:
            # Event handler
            for event in pygame.event.get():
                #############
                # Game QUIT #
                #############
                if event.type == QUIT:
                    if self.user_data_f: # Close current file no matter what
                        self.user_data_f.close()
                    if CONNECTED and not SERVER: # Client mode
                        STOP_GAME = True
                        while CONNECTED:
                            pygame.event.pump()
                            self.connection.join()
                    elif SERVER: # Server Mode
                        self.close_server()
                        self.connection.join()
                    sys.exit()
                if event.type == KEYDOWN and event.key == K_ESCAPE: # Quit game
                    if self.user_data_f: # Close current file no matter what
                        self.user_data_f.close()
                    if current_screen in ['game_play', 'multi_end']: # Reload all multiplayer data
                        if multiplayer:
                            # Multiplayer Mode
                            if CONNECTED and not SERVER: # Client
                                STOP_GAME = True
                                while CONNECTED:
                                    pygame.event.pump()
                                self.connection.join()
                            elif SERVER: # Server Mode
                                self.close_server()
                                self.connection.join()
                            # Restore all attributes
                            self.restore_global_var()
                            self.multiplayer_game_sprite_init()
                            self.multiplayer_main_sprite_init()
                        self.start_sprite_init()
                        self.game_sprite_init()
                        obj_creation = 0 # Controls object creation during the gameplay
                        current_screen = 'start_screen'
                        status = 0
                        played_lost_sound = False
                        pause = False
                        multiplayer = False
                    elif current_screen in ['start_screen']:
                        sys.exit()
                #################
                # Volume Events #
                #################
                if event.type == MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    rect = self.volumn_button.rect
                    img_dim = self.volumn_button.image.get_size()
                    if (pos[0] in range(rect.left, rect.left + img_dim[0]) and
                        pos[1] in range(rect.top, rect.top + img_dim[1])):
                        self.volumn_button.sound_toggle(self.sounds)
                if (current_screen is not 'start_screen' and event.type == KEYDOWN
                    and event.key == K_m):
                    self.volumn_button.sound_toggle(self.sounds)
                #########################
                # State specific Events #
                #########################
                if current_screen == 'multiconfig': # IMPORTANT: Must be placed before start_screen event check
                    if event.type == KEYDOWN:
                        status = self.multiconfig_screen.keyevent(event, self.screen)
                        if status == -1:
                            multiplayer = False
                            current_screen = 'start_screen'
                        if status == 1:
                            if not self.multiconfig_screen.is_host():
                                status = 2 # Status 1: server, Status 2: client
                            self.multiplayer_game_sprite_init()
                            current_screen = 'udpconnect'
                if current_screen == 'start_screen':
                    status = 0
                    if event.type == KEYDOWN:
                        status = self.start_screen.event_blocking(event)
                    if status == 1: # Proceed to the next screen
                        self.game_sprite_init()
                        # SINGLE PLAYER MODE
                        if self.start_screen.state == 0:
                            self.load_userdata(self.start_screen.username.text)
                            current_screen = 'game_play'
                        # MULTIPLAYER MODE
                        elif self.start_screen.state == 1:
                            self.multiplayer_main_sprite_init()
                            multiplayer = True
                            current_screen = 'multiconfig'
                        # SETTINGS
                        else:
                            self.start_screen.troll = True
                            self.start_screen.change_troll()
                if current_screen == 'highscores':
                    if event.type == KEYDOWN and event.key == K_RETURN:
                        self.game_sprite_init()
                        played_lost_sound = False
                        current_screen = 'game_play'
                if current_screen == 'lost_screen': # If Enter is pressed at lost screen, display highscore
                    if event.type == KEYDOWN and event.key == K_RETURN:
                        # Init and Render highscore
                        highscores = []
                        for user in self.user_data:
                            for highscore in self.user_data[user]['highscore']:
                                highscores.append((user, highscore))
                        self.highscore = Highscore(highscores, (self.username,self.scorepad.score))
                        current_screen = 'highscores'
                if current_screen == 'game_play':
                    if not multiplayer: # Pause is unavailable in multiplayer mode
                        if event.type == KEYDOWN and event.key == K_p: # Pause game
                            pause = not pause

            # End of event handler

            #########################################
            # Graphics Rendering and Game Machanics #
            #########################################
            if current_screen == 'start_screen':
                self.screen.fill((35, 52, 81))
                # Detect events
                keys_pressed = pygame.key.get_pressed()
                self.start_screen.event_unblocking(keys_pressed)
                # Display start screen
                self.start_screen.render(self.screen)
                self.volumn_button.render(self.screen)
                pygame.display.update()
                time.sleep(0.02)
                continue

            if current_screen == 'multiconfig':
                self.screen.fill((35, 52, 81))
                self.multiconfig_screen.render(self.screen)
                pygame.display.update()
                time.sleep(0.02)
                continue

            if current_screen == 'udpconnect':
                self.screen.fill((35, 52, 81))
                self.connecting_screen.render(self.screen)
                pygame.display.update()
                if status > 0: # First loop
                    CLIENT_TIMEOUT = False # Set client_timeout to false to start with
                    self.chicken.set_chickid(self.multiconfig_screen.get_chickid())
                    PLAYER['CHICK_ID'] = self.multiconfig_screen.get_chickid()
                    ip = self.multiconfig_screen.get_ip()
                    port = int(self.multiconfig_screen.get_port())
                    # Spawn a thread for udp connection
                    self.connection = None
                    if status == 1: # Hosting - Chicken at the left
                        PLAYER['XPOS'] = SCREEN_WIDTH/4
                        self.connection = threading.Thread(target=udp_host, args=(ip, port))
                        # Place Self HP and score at the left
                        self.hp.position(96, 15)
                        self.scorepad.position(50, 67)
                        # Place Opp HP and score at the right
                        self.opp_hp.position(SCREEN_WIDTH - 200, 15)
                        self.opp_scorepad.right = True
                        self.opp_scorepad.position(SCREEN_WIDTH - 50, 67) # Needs to be adjusted according to strlen
                    elif status == 2: # Connecting - Chicken at the right
                        PLAYER['XPOS'] = (SCREEN_WIDTH/4) * 3
                        self.connection = threading.Thread(target=init_client, args=(ip, port))
                        # Place Self HP and score at the right
                        self.hp.position(SCREEN_WIDTH - 200, 15)
                        self.scorepad.right = True
                        self.scorepad.position(SCREEN_WIDTH - 50, 67)
                        # Place Opp HP and score at the left
                        self.opp_hp.position(96, 15)
                        self.opp_scorepad.position(50, 67) # Needs to be adjusted according to strlen
                    self.chicken.position(PLAYER['XPOS'])
                    self.connection.start()
                    status = 0
                else: # check if any client has connected to the server
                    if CONNECTED:
                        # Update opponent chicken
                        self.opp_chicken.set_chickid(OPP['CHICK_ID'])
                        current_screen = 'game_play'
                        self.connecting_screen.set_text('')
                    if CLIENT_TIMEOUT: # Attempt to reconnect
                        self.connecting_screen.set_text('Connection failed. Please make sure the server is open.')
                        for i in range(3): # Display the message for a few seconds
                            self.connecting_screen.render(self.screen)
                            pygame.display.update()
                            pygame.event.pump()
                            time.sleep(1)
                        status = 0
                        self.connecting_screen.set_text('')
                        current_screen = 'multiconfig'
                time.sleep(0.1)
                continue

            if current_screen == 'highscores':
                self.backdrop.render(self.screen)
                self.volumn_button.render(self.screen)
                self.highscore.render(self.screen)
                pygame.display.update()
                time.sleep(0.02)
                continue

            # Multiplayer mode - User has lost
            if multiplayer and status == 0:
                if self.hp.hp <= 0 and self.opp_hp.hp <= 0:
                    winner = 'YOU' if self.scorepad.score > self.opp_scorepad.score else 'YOUR OPPONENT'
                    self.win_loss_screen = WinLossScreen(self.scorepad.score, self.opp_scorepad.score)
                    status = 1
                    current_screen = 'multi_end'
                if self.hp.hp <= 0:
                    self.chicken.dead = True
                if self.opp_hp.hp <= 0:
                    self.opp_chicken.dead = True
            # Single mode - User has lost
            if not multiplayer and self.hp.hp <= 0:
                current_screen = 'lost_screen'

            if current_screen == 'multi_end':
                if status == 1 and not SERVER: # Client side game stop
                    STOP_GAME = True
                    status = 0
                if STOP_GAME and SERVER: # Server side game stop
                    self.close_server()
                self.win_loss_screen.render(self.screen)
                pygame.display.update()
                time.sleep(0.5)
                continue

            if current_screen == 'lost_screen':
                # Play lost sound once
                if not played_lost_sound:
                    # Play sound
                    self.sounds['lost'].play(0)
                    # Save user highscore
                    self.user_data[self.username]['highscore'].append(self.scorepad.score)
                    self.user_data_f.seek(0)
                    json.dump(self.user_data, self.user_data_f)
                    # Change lost
                    played_lost_sound = True

                self.backdrop.render(self.screen)
                self.volumn_button.render(self.screen)
                self.lost_screen.render(self.screen)
                pygame.display.update()
                time.sleep(0.1)
                continue

            if current_screen == 'game_play':
                if pause:
                    self.backdrop.render(self.screen)
                    self.chicken.render(self.screen)
                    self.egg_sprites.draw(self.screen)
                    self.stone_egg_sprites.draw(self.screen)
                    self.chick_baby_sprites.draw(self.screen)
                    self.scorepad.render(self.screen)
                    self.hp.render(self.screen)
                    self.volumn_button.render(self.screen)
                    darken_screen = DarkenScreen()
                    darken_screen.render(self.screen)
                    self.pause.render(self.screen)
                    pygame.display.update()
                    time.sleep(0.1)
                    continue

                keys_pressed = pygame.key.get_pressed()
                self.chicken.move(keys_pressed)

                # Drop the objects
                for egg in self.egg_sprites.sprites():
                    egg.drop()
                    if egg.y > SCREEN_HEIGHT + egg.image.get_size()[1]:
                        self.egg_sprites.remove(egg)
                for egg in self.stone_egg_sprites.sprites():
                    egg.drop()
                    if egg.y > SCREEN_HEIGHT + egg.image.get_size()[1]:
                        self.stone_egg_sprites.remove(egg)
                for chick in self.chick_baby_sprites.sprites():
                    chick.drop()
                    if chick.y > SCREEN_HEIGHT + chick.image.get_size()[1]:
                        self.chick_baby_sprites.remove(chick)


                if not multiplayer: # Check Collision - Single Player version:
                    # Check collision - Gold Egg
                    collected = pygame.sprite.spritecollide(self.chicken, self.egg_sprites, True)
                    if collected:
                        self.scorepad.change_score(len(collected))
                        self.sounds['egg_get'].play(0)
                    # Check collision - Stone Egg
                    collected = pygame.sprite.spritecollide(self.chicken, self.stone_egg_sprites, True)
                    if collected:
                        self.hp.change_hp(-2)
                        self.sounds['egg_break'].play(0)
                    # Check collision - Chick Baby
                    collected = pygame.sprite.spritecollide(self.chicken, self.chick_baby_sprites, True)
                    if collected:
                        self.hp.change_hp(3)
                        self.scorepad.change_score(len(collected) * 10)
                        self.sounds['chickbaby'].play(0)
                else: # Check collision - Multiplayer version
                    # Check collision - Gold Egg
                    collected = pygame.sprite.spritecollide(self.chicken, self.egg_sprites, False)
                    opp_collected = pygame.sprite.spritecollide(self.opp_chicken, self.egg_sprites, True)
                    if collected and not self.chicken.dead:
                        self.scorepad.change_score(len(collected))
                        self.sounds['egg_get'].play(0)
                    if opp_collected and not self.opp_chicken.dead:
                        self.sounds['egg_get'].play(0)
                    # Clean up
                    [i.kill() for i in collected if i not in opp_collected]
                    # Check collision - Stone Egg
                    collected = pygame.sprite.spritecollide(self.chicken, self.stone_egg_sprites, False)
                    opp_collected = pygame.sprite.spritecollide(self.opp_chicken, self.stone_egg_sprites, True)
                    if collected and not self.chicken.dead:
                        self.hp.change_hp(-2)
                        self.sounds['egg_break'].play(0)
                    if opp_collected and not self.opp_chicken.dead:
                        self.sounds['egg_break'].play(0)
                    # Clean up
                    [i.kill() for i in collected if i not in opp_collected]
                    # Check collision - Chick Baby
                    collected = pygame.sprite.spritecollide(self.chicken, self.chick_baby_sprites, False)
                    opp_collected = pygame.sprite.spritecollide(self.opp_chicken, self.chick_baby_sprites, True)
                    if collected and not self.chicken.dead:
                        self.hp.change_hp(3)
                        self.scorepad.change_score(len(collected)*10)
                        self.sounds['chickbaby'].play(0)
                    # Clean up
                    if opp_collected and not self.opp_chicken.dead:
                        self.sounds['chickbaby'].play(0)
                    [i.kill() for i in collected if i not in opp_collected]

                    #######################################
                    # Multiplayer global variable updates #
                    #######################################
                    # Update PLAYER['XPOS']
                    PLAYER['XPOS'] = self.chicken.x
                    PLAYER['HP'] = self.hp.hp
                    PLAYER['SCORE'] = self.scorepad.score
                    # Update the position of the opponent
                    if len(OPP['XPOS']) > 0:
                        data = OPP['XPOS'].pop(0)
                        self.opp_chicken.position(data)
                    # Update the HP of the opponent
                    self.opp_hp.hp = OPP['HP']
                    # Update the score of the opponent
                    self.opp_scorepad.score = OPP['SCORE']

                    if SERVER is not None: # Server side timeout machanism
                        SERVER_TIMEOUT += 1
                    if CONNECTED == False or SERVER_TIMEOUT >= 250: # Timeout/Disconnected
                        if CONNECTED and not SERVER: # Multiplayer client mode
                            STOP_GAME = True
                            while CONNECTED: # Wait for the client to close itself
                                pygame.event.pump()
                            self.connection.join()
                        elif SERVER: # Force quit the server
                            self.close_server()
                            self.connection.join()

                        # Revert all players' data except chickid and config data
                        player_chickid = self.chicken.get_chickid()
                        is_host = self.multiconfig_screen.is_host()
                        self.restore_global_var()
                        self.game_sprite_init()
                        self.multiplayer_game_sprite_init()
                        PLAYER['CHICK_ID'] = player_chickid
                        self.chicken.set_chickid(player_chickid)
                        if is_host:
                            status = 1
                            self.connecting_screen.set_text('Lost connection. Reconnecting as a host...')
                        else:
                            status = 2
                            self.connecting_screen.set_text('Lost connection. Reconnecting as a client...')
                        obj_creation = 0
                        current_screen = 'udpconnect'

                # Increment egg counter
                if multiplayer:
                    seeds = None
                    if len(SEEDS) > 0:
                        seeds = SEEDS.pop(0)
                    if obj_creation % 10 == 0 and seeds:
                        # Create a new stone egg
                        egg = StoneEgg(seeds=seeds)
                        self.stone_egg_sprites.add(egg)
                    if obj_creation % 20 == 0 and seeds:
                        # Create a new golden egg
                        egg = GoldEgg(seeds=seeds)
                        self.egg_sprites.add(egg)
                    if obj_creation % 500 == 0 and obj_creation > 0 and seeds:
                        # Create a new chick instance
                        chick = ChickBaby(seed=seeds[0])
                        self.chick_baby_sprites.add(chick)
                    if seeds:
                        obj_creation += 1
                else:
                    obj_creation += 1
                    if obj_creation % 10 == 0:
                        # Create a new stone egg
                        egg = StoneEgg()
                        self.stone_egg_sprites.add(egg)
                    if obj_creation % 20 == 0:
                        # Create a new golden egg
                        egg = GoldEgg()
                        self.egg_sprites.add(egg)
                    if obj_creation % 400 == 0 and obj_creation > 0:
                        # Create a new chick instance
                        chick = ChickBaby()
                        self.chick_baby_sprites.add(chick)

                # Render sprites
                self.backdrop.render(self.screen)
                if multiplayer:
                    self.opp_chicken.render(self.screen)
                    self.opp_hp.render(self.screen)
                    self.opp_scorepad.render(self.screen)
                self.chicken.render(self.screen)
                self.egg_sprites.draw(self.screen)
                self.stone_egg_sprites.draw(self.screen)
                self.chick_baby_sprites.draw(self.screen)
                self.scorepad.render(self.screen)
                self.hp.render(self.screen)
                self.volumn_button.render(self.screen)
                pygame.display.update()
                time.sleep(0.01)

# END OF class Game()

if __name__ == "__main__":
    # Handle commandline arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'FULLSCREEN':
            FULLSCREEN = True
    Game()
