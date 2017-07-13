import pygame
import os, sys
from pygame.locals import *
import socketserver
import socket

def min(a, b):
    return a if a < b else b

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
