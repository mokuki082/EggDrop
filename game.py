import pygame
import os, sys
import random, time, json
from pygame.locals import *
from helper import *
from sprites import *
from conn import *

# Global Variables
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 768
FULLSCREEN = False

'''
Handles the main initialization of the game
'''
class Game:
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
        # Set icon
        pygame.display.set_icon(load_image('icon_64.png')[0])
        # Set application title
        pygame.display.set_caption('Egg Drop')
        # Set screensize/fullscreen
        if FULLSCREEN:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Initialize Game Objects
        self.sprites, self.sprite_ref = load_start_screen()
        self.sound_init()
        self.user = User()
        self.handler = Handler(self.sprites, self.sprites)
        self.loop()

    def loop(self):
        '''
            Available game_states/state_data:
            'START': started:bool,
            'SINGLE_SETTING', 'SINGLE_PLAY'
            'CONN_SETTING', 'CONN', 'MULTI_SETTING', 'MULTI_PLAY'

            Unimplemented game_states:
            'SETTING'
        '''
        game_state = 'START'
        state_data = {}
        played_lost_sound = False
        started = False
        pause = False
        droped_chick = False
        while 1:
            # Event handling
            for event in pygame.event.get():
                ###
                ### Quit game control
                ###
                if event.type == pygame.QUIT:
                    self.user.fclose()
                    sys.exit()
                if event.type == KEYDOWN and event.key == K_ESCAPE: # Quit game
                    self.user.fclose()
                    if not game_state == 'START':
                        game_state = 'START'
                        state_data['started'] = False
                    else:
                        sys.exit()
                ###
                ### Volume control
                ###
                if event.type == MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    rect = self.sprite_ref['VolumeButton'].rect
                    if rect.collidepoint(pos):
                        self.sprite_ref['VolumeButton'].sound_toggle(self.sounds)
                if (not game_state == 'START' and
                    event.type == KEYDOWN and event.key == K_m):
                    self.sprite_ref['VolumeButton'].sound_toggle(self.sounds)
                ###
                ### game_state specific events
                ###
                if game_state == 'START':
                    # Enter username
                    if event.type == KEYDOWN:
                        started = self.start_screen.enter_name(event)
                        if started: # Load user data
                            self.user.load()
                            start_screen = self.sprite_ref['StartScreen']
                            self.user.import_user(start_screen.name)
                            sprites, ref = SpriteLoader.load_single
                            self.handler.sprites += SpriteLoader.load_single_game()[0]
                            game_state = 'game_play'
                        state_data['started'] = started
                if game_state == 'HIGHSCORES':
                    if event.type == KEYDOWN and event.key == K_RETURN:
                        self.game_sprite_init()
                        played_lost_sound = False
                        game_state = 'START'
                if game_state == 'lost_screen': # If Enter is pressed at lost screen, display highscore
                    if event.type == KEYDOWN and event.key == K_RETURN:
                        # Init and Render highscore
                        highscores = []
                        for user in self.user_data:
                            for highscore in self.user_data[user]['highscore']:
                                highscores.append((user, highscore))
                        self.highscore = Highscore(highscores, (self.username,self.scorepad.score))
                        game_state = 'highscore_screen'

                if game_state == 'game_play':
                    if event.type == KEYDOWN and event.key == K_p: # Pause game
                        pause = not pause
            ###
            ### End of event handler
            ###

            if game_state == 'start_screen':
                # Display start screen
                self.screen.fill((35, 52, 81))
                self.volumn_button.draw(self.screen)
                self.start_screen.draw(self.screen)
                pygame.display.update()
                time.sleep(0.02)
                continue

            if game_state == 'highscore_screen':
                self.backdrop.draw(self.screen)
                self.volumn_button.draw(self.screen)
                self.highscore.draw(self.screen)
                pygame.display.update()
                time.sleep(0.02)
                continue

            # User has lost
            if self.hp.hp <= 0:
                game_state = 'lost_screen'

            if game_state == 'lost_screen':
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

                self.backdrop.draw(self.screen)
                self.volumn_button.draw(self.screen)
                self.lost_screen.draw(self.screen)
                pygame.display.update()
                time.sleep(0.1)
                continue

            if game_state == 'game_play':
                if pause:
                    self.backdrop.draw(self.screen)
                    self.chicken.draw(self.screen)
                    self.egg_sprites.draw(self.screen)
                    self.stone_egg_sprites.draw(self.screen)
                    self.chick_baby_sprites.draw(self.screen)
                    self.scorepad.draw(self.screen)
                    self.hp.draw(self.screen)
                    self.volumn_button.draw(self.screen)
                    darken_screen = DarkenScreen()
                    darken_screen.draw(self.screen)
                    self.pause.draw(self.screen)
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
                self.backdrop.draw(self.screen)
                self.chicken.draw(self.screen)
                self.egg_sprites.draw(self.screen)
                self.stone_egg_sprites.draw(self.screen)
                self.chick_baby_sprites.draw(self.screen)
                self.scorepad.draw(self.screen)
                self.hp.draw(self.screen)
                self.volumn_button.draw(self.screen)
                pygame.display.update()
                time.sleep(0.01)



if __name__ == "__main__":
    # Handle commandline arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'FULLSCREEN':
            FULLSCREEN = True

    Game()
