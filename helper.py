import pygame
import os, sys
from pygame.locals import *
import json

def min(a, b):
    return a if a < b else b


#################
### Load Data ###
#################

''' Load an animation strip.'''
def load_strip(filename, nframes, width=None, height=None, colorkey=None):
    full_image, full_rect = load_image(filename, width=width, height=height)
    sub_images = []
    for i in range(nframes):
        sub_w, sub_h = full_image.get_size()[0]/nframes, full_image.get_size()[1]
        sub_image = pygame.Surface((sub_w, sub_h))
        sub_image.blit(full_image, (-i * sub_w, 0, sub_w, sub_h))
        if colorkey:
            sub_image.set_colorkey(colorkey)
        sub_rect = sub_image.get_rect()
        sub_images.append((sub_image, sub_rect))
    return sub_images

def load_image(filename, width=None, height=None):
    fullpath = os.path.join('img', filename)
    try:
        image = pygame.image.load(fullpath)
    except pygame.error:
        print('Cannot load image:', fullpath)
        raise SystemError
    image = image.convert_alpha()
    # Resize image if specified
    if width and height:
        image = pygame.transform.scale(image, (width, height))
    if width:
        ratio = width/image.get_size()[0]
        image = pygame.transform.scale(image, (width, int(image.get_size()[1] * ratio)))
    elif height:
        ratio = height/image.get_size()[1]
        image = pygame.transform.scale(image, (int(image.get_size()[0] * ratio), height))

    return image, image.get_rect()

def load_music(filename):
    fullpath = os.path.join('snd', filename)
    return pygame.mixer.Sound(fullpath)

####################
### Load Sprites ###
####################

class SpriteLoader():
    ''' Convert a list of sprites into Classname:sprite '''
    def as_dict(sprites):
        return {i.__class__.__name__ : i for i in sprites}

    ''' Load the sprites necessary for start_screen '''
    def load_start_screen():
        sprites = [Backdrop(), VolumeButton(), StartScreen()]
        return sprites, self.as_dict(sprites)

    def load_single_game():
        sprites =  [Chicken(), Scorepad(), HPBar(), Pause(), pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()]
        return sprites, self.as_dict(sprites)

    def load_multi_game():
        # TODO: List of sprites for multiplayer
        return []

    def load_lost():
        return [LostScreen()]


#######################
### Handler Classes ###
#######################

''' Handles rendering and static movements '''
class Handler():
    def __init__(self, sprites, screen):
        self.sprites = sprites
        self.screen = screen

    def render(self):
        for i in self.sprites:
            i.draw(self.screen)

    def update(self):
        for i in self.sprites:
            i.update()

##################
### User Class ###
##################
''' Handles User data reading/writing '''
class User():
    def __init__(self):
        self.data_f = None
        self.data = None
        self.username = None

    def load(self):
        path = os.path.join('data', 'user_data')
        self.data_f = open(path, 'r+')
        self.data = json.load(self.data_f)

    def fclose(self):
        if self.data_f:
            self.data_f.close()

    def import_user(self, username):
        if username not in self.data:
            self.data[username] = { "volume": True,
                                    "highscore": [],
                                    "screen_width": SCREEN_WIDTH,
                                    "screen_height": SCREEN_HEIGHT})
        self.username = username
