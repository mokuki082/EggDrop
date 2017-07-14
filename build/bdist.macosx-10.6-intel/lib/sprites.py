import pygame
import os, sys
import random, time
from pygame.locals import *
from helper import *
from sprites import *

SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 768
FONT = os.path.join('fonts', 'WorkSans-ExtraBold.ttf')

''' Place a surface at the center of the screen '''
def place_center(surface, rect):
    rect.move_ip(SCREEN_WIDTH/2 - surface.get_size()[0]/2,
                SCREEN_HEIGHT/2 - surface.get_size()[1]/2)

''' Position a surface based on its midpoint '''
def position_mid(surface, rect, x, y):
    rect.move_ip(x - rect.left - surface.get_size()[0]/2, y - rect.top - surface.get_size()[1]/2)

''' Position a surface based on its left point'''
def position_left(surface, rect, x, y):
    rect.move_ip(x - rect.left, y - rect.top)

''' Position an object randomly at the top, returns its new x-coordinate '''
def position_rand_top(surface, rect):
    x = random.randint(int(surface.get_size()[0] / 2), int(SCREEN_WIDTH - surface.get_size()[0]))
    position_mid(surface, rect, x, 0)
    return x

class ChickBaby(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.nframes = 5
        self.frames = load_strip('chicken_babies.png', self.nframes, colorkey=(255,255,255))
        self.frame_counter = 0
        self.frame_duration = 1
        # Position the chick baby at a randomized position
        self.x = position_rand_top(self.frames[0][0], self.frames[0][1])
        self.y = 0
        for frame in self.frames[1:]:
            position_mid(frame[0], frame[1], self.x, 0)
        self.image = self.frames[0][0]
        self.rect = self.frames[0][1]
        self.y_dist = 3

    def drop(self):
        for frame in self.frames:
            frame[1].move_ip(0, self.y_dist)
        self.y += self.y_dist
        self.image = self.frames[self.frame_counter % self.nframes][0]
        self.rect = self.frames[self.frame_counter % self.nframes][1]
        self.frame_counter += 1

class Pause(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('pause.png')
        place_center(self.image, self.rect)
    def render(self, screen):
        screen.blit(self.image, (self.rect))

class Record(pygame.sprite.Sprite):
    def __init__(self, rank, username_highscore, fontcolor=(21, 29, 40)):
        pygame.sprite.Sprite.__init__(self)
        self.frames = load_strip('highscore_recordbar.png', 5)
        # position record
        self.yoffset = 140
        self.place(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - self.yoffset + (rank - 1) * 2 * self.frames[0][0].get_size()[1])
        self.rank = rank
        self.username = username_highscore[0]
        self.score = username_highscore[1]
        self.font = pygame.font.Font(FONT, 20)
        self.rank_render = self.font.render(str(self.rank), True, fontcolor)
        self.username_render = self.font.render(self.username, True, fontcolor)
        self.score_render = self.font.render(str(self.score), True, fontcolor)
        self.duration = 1.5 # Duration per frame
        self.frame_count = 0

    def place(self, x, y):
        for image, rect in self.frames:
            position_mid(image, rect, x, y)

    def render(self, screen):
        frame = self.frames[int(self.frame_count/self.duration)]
        screen.blit(frame[0], frame[1])
        if self.frame_count <= 4 * self.duration - 1:
            self.frame_count += 1
            return False # Haven't finished animation
        # Finished Animation
        top = SCREEN_HEIGHT/2 - self.yoffset - 10 + (self.rank - 1) * 2 * self.frames[0][0].get_size()[1]
        screen.blit(self.rank_render, (SCREEN_WIDTH/2 - 140, top))
        screen.blit(self.username_render, (SCREEN_WIDTH/2 - 80, top))
        screen.blit(self.score_render, (SCREEN_WIDTH/2 + 100, top))
        return True # Finished rendering


class Highscore(pygame.sprite.Sprite):
    '''
    Highscores is a list of (user,score) pairs
    curr is a (user,score) pair of the current gameplay
    '''
    def __init__(self, highscores, curr):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('highscore_board.png')
        self.records = []
        highscores.sort(key=lambda x: x[1], reverse=True)
        user_record = True
        for i in range(min(len(highscores), 5)):
            color = (21, 29, 40)
            if highscores[i] == curr and user_record:
                color = (185, 71, 46)
                user_record = False
            record = Record(i + 1, highscores[i], fontcolor=color)
            self.records.append(record)
        self.highscores = highscores # List of highscore and username pairs
        # Position images
        place_center(self.image, self.rect)

    def compare(tuple_a, tuple_b):
        if tuple_a[1] == tuple_b[1]:
            return 0
        return 1 if tuple_a[1] > tuple_b[1] else -1

    def render(self, screen):
        screen.blit(self.image, self.rect)
        for i in self.records:
            if not i.render(screen):
                return
            i.render(screen)


class StartScreen(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('start_screen.png')
        # Position image at the center of the screen
        place_center(self.image, self.rect)
        self.name = ""
        self.font = pygame.font.Font(FONT, 26)
        self.blinker = pygame.Surface((13, 25))
        self.blinker.fill((21, 29, 40))
        self.blinker_counter = 0
        self.blinker_duration = 35

    def render(self, screen):
        # Render image
        screen.blit(self.image, (self.rect))
        # Render text
        self.name_render = self.font.render(self.name, True, (21, 29, 40))
        screen.blit(self.name_render, (SCREEN_WIDTH/2 - 75, SCREEN_HEIGHT/2 + 35))
        if self.blinker_counter < self.blinker_duration/2:
            # Position blinker after text
            screen.blit(self.blinker, (self.blinker.get_rect(
                            topleft=(SCREEN_WIDTH/2 - 75 + self.name_render.get_size()[0],
                                    SCREEN_HEIGHT/2 + 37))))
        if self.blinker_counter < self.blinker_duration:
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
        pygame.sprite.Sprite.__init__(self)
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

class DarkenScreen(pygame.sprite.Sprite):
    def __init__(self, color=(35, 52, 81)):
        pygame.sprite.Sprite.__init__(self)
        self.background_darken = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.background_darken.set_alpha(200)
        self.background_darken.fill(color)
    def render(self, screen):
        screen.blit(self.background_darken, (0,0))

class LostScreen(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('lost_screen.png')
        self.darken = DarkenScreen()
        # Move banner to center
        place_center(self.image, self.rect)

    def render(self, screen):
        # Darken the background
        self.darken.render(screen)
        screen.blit(self.image, (self.rect))


class HPBar(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
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
        pygame.sprite.Sprite.__init__(self)
        # Initialize font
        self.font = pygame.font.Font(FONT, 32)
        self.score = 0

    def render(self, screen):
        string = "Score: " + str(self.score)
        scorepad = self.font.render(string, True, (95,92,119))
        screen.blit(scorepad, (50, 10))

class Egg(pygame.sprite.Sprite):
    def __init__(self, filename, width=None, height=None, drop_vel=10):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image(filename, width=width, height=height)
        self.x = position_rand_top(self.image, self.rect)
        self.y = 0
        self.y_dist = drop_vel

    def drop(self):
        self.rect.move_ip(0, self.y_dist)
        self.y += self.y_dist

    def render(self, screen):
        screen.blit(self.image, (self.rect))


class StoneEgg(Egg):
    def __init__(self):
        super().__init__('stone_egg_40.png', height=60, drop_vel=random.randint(10,15))

class GoldEgg(Egg):
    def __init__(self):
        super().__init__('gold_egg_30.png', height=35, drop_vel=random.randint(3,10))


class Backdrop(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('backdrop_1080.jpg', width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.vel_x = 0
        self.vel_y = 0

    def render(self, screen):
        screen.blit(self.image, (self.rect))

class Chicken(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('chicken_120.png', width=120, height=120)
        # Set the number of pixels to move each time
        self.x_dist = 10
        self.x, self.y = 0, 0
        # Place chicken at the bottom center of the page
        self.position(SCREEN_WIDTH/2, SCREEN_HEIGHT - 180)

    ''' Place sprite at exactly the coordinates specified '''
    def position(self, x, y):
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
