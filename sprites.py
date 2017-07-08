import pygame
import os, sys
import random, time
from pygame.locals import *
from helper import *
from sprites import *

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 700
FONT = os.path.join('fonts', 'WorkSans-ExtraBold.ttf')

''' Position a surface at the center of the screen '''
def position_center(surface, rect):
    rect.move_ip(SCREEN_WIDTH/2 - surface.get_size()[0]/2,
                SCREEN_HEIGHT/2 - surface.get_size()[1]/2)

class HighScore(pygame.sprite.Sprite):
    def __init__(self):
        self.back_image, self.back_rect = load_image('highscore_board.png')

class StartScreen(pygame.sprite.Sprite):
    def __init__(self):
        self.image, self.rect = load_image('start_screen.png')
        # Position image at the center of the screen
        position_center(self.image, self.rect)
        self.name = ""
        self.font = pygame.font.Font(FONT, 26)
        self.blinker = pygame.Surface((13, 25))
        self.blinker.fill((21, 29, 40))
        self.blinker_counter = 0

    def render(self, screen):
        # Render image
        screen.blit(self.image, (self.rect))
        # Render text
        self.name_render = self.font.render(self.name, True, (21, 29, 40))
        screen.blit(self.name_render, (SCREEN_WIDTH/2 - 75, SCREEN_HEIGHT/2 + 35))
        if self.blinker_counter < 50:
            # Position blinker after text
            screen.blit(self.blinker, (self.blinker.get_rect(
                            topleft=(SCREEN_WIDTH/2 - 75 + self.name_render.get_size()[0],
                                    SCREEN_HEIGHT/2 + 37))))
        if self.blinker_counter < 100:
            self.blinker_counter += 1
        else:
            self.blinker_counter = 0

    ''' User entering data, returns true if user enters K_RETURN '''
    def enter_name(self, event):
        if len(self.name) <= 13 and event.unicode.isalpha():
            self.name += event.unicode
        elif event.key == K_BACKSPACE:
            self.name = self.name[:-1]
        elif event.key == K_RETURN:
            return True
        return False


class VolumnButton(pygame.sprite.Sprite):
    def __init__(self):
        self.images = []
        self.images.append(load_image('sound_on.png', width=40, height=40))
        self.images.append(load_image('sound_off.png', width=40, height=40))
        # Set position for both on and off
        self.images[0][1].move_ip(30, SCREEN_HEIGHT - self.images[0][0].get_size()[1] - 30)
        self.images[1][1].move_ip(30, SCREEN_HEIGHT - self.images[1][0].get_size()[1] - 30)
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
        self.background_darken.fill((35, 52, 81))
        # Move banner to center
        position_center(self.image, self.rect)

    def render(self, screen):
        # Darken the background
        screen.blit(self.background_darken, (0,0))
        screen.blit(self.image, (self.rect))


class HPBar(pygame.sprite.Sprite):
    def __init__(self):
        self.hp = 10
        self.font = pygame.font.Font(FONT, 32)
        self.blood_color = (186,71,46)
        self.hp_text = self.font.render("HP", True, self.blood_color)

    def render(self, screen):
        screen.blit(self.hp_text, (SCREEN_WIDTH - 250, 10))
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
