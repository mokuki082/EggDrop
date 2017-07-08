import pygame
import os, sys
from pygame.locals import *

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
    return image, image.get_rect()

def load_music(filename):
    fullpath = os.path.join('snd', filename)
    return pygame.mixer.Sound(fullpath)
