import pygame
import os, sys
from pygame.locals import *
from helpers import *
import random
import time

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FULLSCREEN = False
SET_LOST = True
FONT = os.path.join('fonts', 'WorkSans-ExtraBold.ttf')

class VolumnButton(pygame.sprite.Sprite):
    def __init__(self):
        self.images = []
        self.images.append(load_image('sound_on.png', width=40, height=40))
        self.images.append(load_image('sound_off.png', width=40, height=40))
        # Set position for both on and off
        self.images[0][1].move_ip(30, SCREEN_HEIGHT - self.images[0][0].get_size()[1] - 50)
        self.images[1][1].move_ip(30, SCREEN_HEIGHT - self.images[1][0].get_size()[1] - 50)
        # Set current image/rect
        self.image = self.images[0][0]
        self.rect = self.images[0][1]
        self.sound_on = True

    def sound_toggle(self, sounds):
        if self.sound_on:
            self.image = self.images[1][0]
            self.rect = self.images[1][1]
            for key in sounds:
                sounds[key].set_volume(0)
        else:
            self.image = self.images[0][0]
            self.rect = self.images[0][1]
            for key in sounds:
                sounds[key].set_volume(1)
        self.sound_on = not self.sound_on

    def render(self, screen):
        screen.blit(self.image, (self.rect))

class LostScreen(pygame.sprite.Sprite):
    def __init__(self):
        self.image, self.rect = load_image('lost_screen.png')
        self.background_darken = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.background_darken.set_alpha(200)
        self.background_darken.fill((0,0,0))
        # Move banner to center
        self.rect.move_ip(SCREEN_WIDTH/2 - self.image.get_size()[0]/2,
                        SCREEN_HEIGHT/2 - self.image.get_size()[1]/2)

    def render(self, screen):
        # Darken the background
        screen.blit(self.background_darken, (0,0))
        screen.blit(self.image, (self.rect))


class HPBar(pygame.sprite.Sprite):
    def __init__(self):
        self.hp = 10
        self.font = pygame.font.Font(FONT, 32)
        self.blood_color = (186,71,46)

    def render(self, screen):
        scorepad = self.font.render("HP", True, self.blood_color)
        screen.blit(scorepad, (SCREEN_WIDTH - 250, 10))
        rect_space = (SCREEN_WIDTH - 200, 15, 150, 32)
        pygame.draw.rect(screen, (255,255,255), rect_space)
        if self.hp > 0:
            rect_blood = (SCREEN_WIDTH - 200, 15, self.hp * 15, 32)
            pygame.draw.rect(screen, self.blood_color, rect_blood)


class Scorepad(pygame.sprite.Sprite):
    def __init__(self):
        # Initialize font
        self.font = pygame.font.Font(FONT, 32)
        self.score = 0

    def render(self, screen):
        string = "Score: " + str(self.score)
        scorepad = self.font.render(string, True, (95,92,119))
        screen.blit(scorepad, (50, 10))

class Egg(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('egg_128.png', width=30, height=30)
        self.x = 0
        self.y = 0
        self.y_dist = random.randint(3,10)
        self.rand_place()

    ''' Randomly place the egg at the top of the screen '''
    def rand_place(self):
        x = random.randint(self.image.get_size()[0] / 2, SCREEN_WIDTH - self.image.get_size()[0])
        self.rect.move_ip(x - self.x, 0)
        self.x = x

    def drop(self):
        self.rect.move_ip(0, self.y_dist)
        self.y += self.y_dist

    def render(self, screen):
        screen.blit(self.image, (self.rect))


class Backdrop(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('backdrop_3840.png', width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.vel_x = 0
        self.vel_y = 0

    def render(self, screen):
        screen.blit(self.image, (self.rect))

class Chicken(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('chicken_512.png', width=120, height=120)
        # Set the number of pixels to move each time
        self.x_dist = 10
        self.x, self.y = 0, 0

    ''' Place sprite at exactly the coordinates specified '''
    def place(self, x, y):
        self.rect.move_ip(x - self.x, y - self.y)
        self.x, self.y = x, y

    ''' Key is the pygame define for either left/right '''
    def move(self, keys):
        xMove = 0
        if ((keys[K_RIGHT] or keys[K_d]) and self.x < SCREEN_WIDTH - self.image.get_size()[0]):
            xMove = self.x_dist
            self.x += self.x_dist
        elif ((keys[K_LEFT] or keys[K_a]) and self.x > 0):
            xMove = -self.x_dist
            self.x -= self.x_dist
        self.rect.move_ip(xMove, 0)

    def render(self, screen):
        screen.blit(self.image, (self.rect))


'''
Handles the main initialization of the game
'''
class Game:
    def sprite_init(self):
        # Initialize backdrop
        self.backdrop = Backdrop()
        # Initialize chicken
        self.chicken = Chicken()
        # Place chicken at the bottom center of the page
        c_width, c_height = self.chicken.image.get_size()
        self.chicken.place(self.width/2 - c_width/2, self.height - c_height - 80)
        self.egg_sprites = pygame.sprite.Group()
        # Initialize scorepad
        self.scorepad = Scorepad()
        # Initialize hp
        self.hp = HPBar()
        self.lost_screen = LostScreen()
        # Initialize volumn button
        self.volumn_button = VolumnButton()

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
        #Initialize background and sprites
        self.sprite_init()
        self.sound_init()
        self.loop()
        # Initialize background music and sound effects
        self.back_msc = pygame.mixer.music.load()

    def loop(self):
        egg_creation = 0
        lost_sound_played = False
        while 1:
            # Event handler
            for event in pygame.event.get():
                if (event.type == pygame.QUIT or
                    (event.type == KEYDOWN and event.key == K_ESCAPE)):
                    sys.exit()
                if self.hp.hp <= 0: # If Enter is pressed at lost screen, reset and start again
                    if event.type == KEYDOWN and event.key == K_RETURN:
                        self.sprite_init()
                if event.type == MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    rect = self.volumn_button.rect
                    img_dim = self.volumn_button.image.get_size()
                    if (pos[0] in range(rect.left, rect.left + img_dim[0]) and
                        pos[1] in range(rect.top, rect.top + img_dim[1])):
                        self.volumn_button.sound_toggle(self.sounds)
            # Check HP
            if self.hp.hp <= 0:
                # Play lost sound once
                if not lost_sound_played:
                    self.sounds['lost'].play(0)
                    lost_sound_played = True
                # TODO: Display end score (You saved 50 eggs etc)
                self.backdrop.render(self.screen)
                self.chicken.render(self.screen)
                self.egg_sprites.draw(self.screen)
                self.scorepad.render(self.screen)
                self.hp.render(self.screen)
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
            if egg_creation == 60:
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
