import pygame
import os, sys
import random, time, json
from pygame.locals import *
from helper import *
from sprites import *

# Global Variables
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 700
FULLSCREEN = False

'''
Handles the main initialization of the game
'''
class Game:

    def sprite_init(self):
        # Initialize backdrop
        self.backdrop = Backdrop()
        # Initialize chicken
        self.chicken = Chicken()
        self.egg_sprites = pygame.sprite.Group()
        # Initialize scorepad
        self.scorepad = Scorepad()
        # Initialize hp
        self.hp = HPBar()
        self.lost_screen = LostScreen()
        # Initialize volumn button
        self.volumn_button = VolumnButton()
        # Initialize start screen
        self.start_screen = StartScreen()

    def sound_init(self):
        # Initialize sound
        self.sounds = {'background': load_music('background.wav'),
                    'egg_get': load_music('egg_get.wav'),
                    'egg_break': load_music('egg_break.wav'),
                    'lost': load_music('lost.wav')}
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
        self.sprite_init()
        self.sound_init()
        self.user_data_f = None
        self.user_data = None
        self.username = None
        self.clock = pygame.time.Clock()
        self.loop()

    def loop(self):
        egg_creation = 0
        current_screen = 'start_screen'
        played_lost_sound = False
        started = False
        while 1:
            self.clock.tick(25)
            # Event handler
            for event in pygame.event.get():
                if (event.type == pygame.QUIT or
                    (event.type == KEYDOWN and event.key == K_ESCAPE)):
                    if self.user_data_f:
                        self.user_data_f.close()
                    sys.exit()
                if current_screen == 'highscore_screen':
                    if event.type == KEYDOWN and event.key == K_RETURN:
                        self.sprite_init()
                        lost = False
                if current_screen == 'lost_screen': # If Enter is pressed at lost screen, display highscore
                    if event.type == KEYDOWN and event.key == K_RETURN:
                        # Init and Render highscore
                        highscores = []
                        for user in self.user_data:
                            for highscore in self.user_data[user]['highscore']:
                                highscores.append((user, highscore))
                        self.highscore = Highscore(highscores)
                        current_screen = 'highscore_screen'
                if event.type == MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    rect = self.volumn_button.rect
                    img_dim = self.volumn_button.image.get_size()
                    if (pos[0] in range(rect.left, rect.left + img_dim[0]) and
                        pos[1] in range(rect.top, rect.top + img_dim[1])):
                        self.volumn_button.sound_toggle(self.sounds)
                if current_screen == 'start_screen':
                    # Enter username
                    if event.type == KEYDOWN:
                        started = self.start_screen.enter_name(event)
                        if started: # Load user data
                            fname = os.path.join('data', 'user_data.json')
                            self.user_data_f = open(fname, 'r+')
                            self.user_data = json.load(self.user_data_f)
                            if self.start_screen.name not in self.user_data:
                                self.user_data[self.start_screen.name] = {"volume": True,
                                                                        "highscore": [],
                                                                        "screen_width": SCREEN_WIDTH,
                                                                        "screen_height": SCREEN_HEIGHT}
                            self.username = self.start_screen.name
                            current_screen = 'game_play'

            if current_screen == 'start_screen':
                # Display start screen
                self.volumn_button.render(self.screen)
                self.start_screen.render(self.screen)
                pygame.display.update()
                continue

            if current_screen == 'highscore_screen':
                self.backdrop.render(self.screen)
                self.volumn_button.render(self.screen)
                self.highscore.render(self.screen)
                pygame.display.update()
                continue

            # User has lost
            if self.hp.hp <= 0:
                current_screen = 'lost_screen'

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
                continue

            keys_pressed = pygame.key.get_pressed()
            self.chicken.move(keys_pressed)

            # Drop the eggs on the screen
            for egg in self.egg_sprites.sprites():
                egg.drop()
                if egg.y > SCREEN_HEIGHT + egg.image.get_size()[1]:
                    self.hp.hp -= 1
                    self.egg_sprites.remove(egg)
                    self.sounds['egg_break'].play(0)

            # Check collision - and kill the eggs if they collide
            collected_eggs = pygame.sprite.spritecollide(self.chicken, self.egg_sprites, True)
            if collected_eggs:
                self.scorepad.score += len(collected_eggs)
                self.sounds['egg_get'].play(0)

            # Increment egg counter
            egg_creation += 1
            if egg_creation == 20:
                # Create a new egg
                egg = Egg()
                self.egg_sprites.add(egg)
                egg_creation = 0

            # Render sprites
            self.backdrop.render(self.screen)
            self.chicken.render(self.screen)
            self.egg_sprites.draw(self.screen)
            self.scorepad.render(self.screen)
            self.hp.render(self.screen)
            self.volumn_button.render(self.screen)
            pygame.display.update()



if __name__ == "__main__":
    Game()
