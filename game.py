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
        #########################
        # Dropping Game Objects #
        #########################
        # Initialize eggs (gold)
        self.egg_sprites = pygame.sprite.Group()
        # Initialize rock eggs
        self.stone_egg_sprites = pygame.sprite.Group()
        # Initialize chick babies
        self.chick_baby_sprites = pygame.sprite.Group()


    def start_sprite_init(self):
        # Initialize backdrop
        self.backdrop = Backdrop()
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
        self.start_sprite_init()
        self.sound_init()
        self.user_data_f = None
        self.user_data = None
        self.username = None
        self.clock = pygame.time.Clock()
        self.loop()

    def loop(self):
        obj_creation = 0 # Controls object creation during the gameplay
        current_screen = 'start_screen'
        played_lost_sound = False
        started = False
        pause = False
        droped_chick = False
        while 1:
            self.clock.tick(25)
            # Event handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.user_data_f: # Close current file no matter what
                        self.user_data_f.close()
                    sys.exit()
                if event.type == KEYDOWN and event.key == K_ESCAPE: # Quit game
                    if self.user_data_f: # Close current file no matter what
                        self.user_data_f.close()
                    if current_screen == 'game_play':
                        current_screen = 'start_screen'
                        started = False
                    else:
                        sys.exit()
                if event.type == MOUSEBUTTONUP: # Control volumes
                    pos = pygame.mouse.get_pos()
                    rect = self.volumn_button.rect
                    img_dim = self.volumn_button.image.get_size()
                    if (pos[0] in range(rect.left, rect.left + img_dim[0]) and
                        pos[1] in range(rect.top, rect.top + img_dim[1])):
                        self.volumn_button.sound_toggle(self.sounds)
                if (current_screen is not 'start_screen' and event.type == KEYDOWN
                    and event.key == K_m):
                    self.volumn_button.sound_toggle(self.sounds)
                if current_screen == 'highscore_screen':
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
                        current_screen = 'highscore_screen'
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
                            self.game_sprite_init()
                            current_screen = 'game_play'
                if current_screen == 'game_play':
                    if event.type == KEYDOWN and event.key == K_p: # Pause game
                        pause = not pause
            # End of event handler

            if current_screen == 'start_screen':
                # Display start screen
                self.screen.fill((35, 52, 81))
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
                        self.chick_baby_sprites.remove(egg)

                # Check collision - Gold Egg
                collected = pygame.sprite.spritecollide(self.chicken, self.egg_sprites, True)
                if collected:
                    self.scorepad.score += len(collected)
                    self.sounds['egg_get'].play(0)
                # Check collision - Stone Egg
                collected = pygame.sprite.spritecollide(self.chicken, self.stone_egg_sprites, True)
                if collected:
                    self.hp.hp -= 2
                    self.sounds['egg_break'].play(0)
                # Check collision - Chick Baby
                collected = pygame.sprite.spritecollide(self.chicken, self.chick_baby_sprites, True)
                if collected:
                    if self.hp.hp + 3 > 10:
                        self.hp.hp = 10
                    else:
                        self.hp.hp += 3
                    self.scorepad.score += len(collected) * 10
                    self.sounds['egg_get'].play(0)

                obj_creation += 1
                # Increment egg counter
                if obj_creation % 30 == 0:
                    # Create a new golden egg
                    egg = GoldEgg()
                    self.egg_sprites.add(egg)
                if obj_creation % 10 == 0:
                    # Create a new stone egg
                    egg = StoneEgg()
                    self.stone_egg_sprites.add(egg)
                if self.scorepad.score > 0 and self.scorepad.score % 25 == 0 and not droped_chick:
                    droped_chick = True
                    # Create a new chick instance
                    chick = ChickBaby()
                    self.chick_baby_sprites.add(chick)
                elif not self.scorepad.score % 25 == 0:
                    droped_chick = False

                # Render sprites
                self.backdrop.render(self.screen)
                self.chicken.render(self.screen)
                self.egg_sprites.draw(self.screen)
                self.stone_egg_sprites.draw(self.screen)
                self.chick_baby_sprites.draw(self.screen)
                self.scorepad.render(self.screen)
                self.hp.render(self.screen)
                self.volumn_button.render(self.screen)
                pygame.display.update()



if __name__ == "__main__":
    # Handle commandline arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'FULLSCREEN':
            FULLSCREEN = True

    Game()
