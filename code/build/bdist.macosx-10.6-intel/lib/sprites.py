import pygame
import os, sys, traceback
import random, time
from pygame.locals import *
from helper import *
from sprites import *

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FONT = os.path.join('fonts', 'WorkSans-ExtraBold.ttf')

def min(a, b):
    return a if a < b else b

''' Return a random integfer between min and max inclusively '''
def randint(min, max, seed=-1):
    if seed >= 0:
        random.seed(seed)
    return random.randint(min, max)

''' Place a surface at the center of the screen '''
def position_centre(surface, rect):
    rect.move_ip(SCREEN_WIDTH/2 - surface.get_size()[0]/2,
                SCREEN_HEIGHT/2 - surface.get_size()[1]/2)

''' Position a surface based on its midpoint '''
def position_mid(surface, rect, x, y):
    rect.move_ip(x - rect.left - surface.get_size()[0]/2, y - rect.top - surface.get_size()[1]/2)

''' Position a surface based on its left point'''
def position_left(surface, rect, x, y):
    rect.move_ip(x - rect.left, y - rect.top)

''' Position an object randomly at the top, returns its new x-coordinate '''
def position_rand_top(surface, rect, seed=-1):
    if seed >= 0:
        random.seed(seed)
    x = randint(int(surface.get_size()[0] / 2), int(SCREEN_WIDTH - surface.get_size()[0]))
    position_mid(surface, rect, x, 0)
    return x

def mod(n):
    return n if n >= 0 else -n

class ChickBaby(pygame.sprite.Sprite):
    def __init__(self, seed=-1):
        pygame.sprite.Sprite.__init__(self)
        self.nframes = 8
        self.frames = load_strip('chicken_babies.png', self.nframes, colorkey=(255,255,255))
        self.frame_counter = 0
        self.frame_duration = 1
        # Position the chick baby at a randomized position
        self.x = position_rand_top(self.frames[0][0], self.frames[0][1], seed=seed)
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
        position_centre(self.image, self.rect)
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
        position_centre(self.image, self.rect)

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
    def __init__(self, sound, troll_snd):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('start_screen.png')
        self.sound = sound
        self.troll_snd = troll_snd
        self.state = 0 # 0: single player, 1: multiplayer, 2: hints
        # Position image at the center of the screen
        position_centre(self.image, self.rect)
        # Initialize text
        self.username = TextBox(fontsize=30, fontcolor=(21, 29, 40), blinker=True)
        self.username.position_left(SCREEN_WIDTH/2 - 120, SCREEN_HEIGHT/2 - 113)
        # Initialize buttons
        pos = (SCREEN_WIDTH/2 - 300, SCREEN_HEIGHT/2 + 150)
        btn_1player = Button('btn_1player', pos, selected=True, width=SCREEN_WIDTH/3+20)
        pos = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 150)
        btn_2players = Button('btn_2players', pos, width=SCREEN_WIDTH/3+20)
        pos = (SCREEN_WIDTH/2 + 300, SCREEN_HEIGHT/2 + 150)
        btn_hints = Button('btn_hints', pos, width=SCREEN_WIDTH/3+20)
        self.buttons = [btn_1player, btn_2players, btn_hints]
        self.hints = TextBox(fontsize=20, fontcolor=(49,82,128))
        self.troll = False
        self.troll_c = -1
        self.msgs = ["Nah, you don't need hints",
                    "I told you you don't need hints!",
                    "You see, this game is intuitive",
                    "Surely you'll know how to play it",
                    "Stop asking for hints!",
                    "Stop asking for hints!",
                    "Stop asking for hints!",
                    "Stop asking for hints!",
                    "Just. Play.",
                    "If you press me again I'll be mad",
                    "Do you really want me to be mad?",
                    "...",
                    "Okay, you win.",
                    "I do actually have ONE hint.",
                    "Would you like to know about it?",
                    "Are you sure? You will regret this.",
                    "It's a boring hint anyway.",
                    "Do you really want to know?",
                    "But what if you already know this",
                    "Then I'll look stupid.",
                    "Alright, don't laugh at me.",
                    "Promise not to laugh at me.",
                    "Okay, Here we go.",
                    "Press 'M' to mute the annoying music.",
                    "Oh, and it doesn't work here",
                    "Use your cusor here instead.",
                    "That's it.",
                    "Boring huh?",
                    "I told you it's no fun.",
                    "What, you want another hint?",
                    "There's no more.",
                    "Really, there's no more.",
                    "If you keep pressing Moku might get mad",
                    "Hmm? you ask who Moku is?",
                    "She is the developer of this game",
                    "She also drew everything.",
                    "I love her.",
                    "She is just so wonderful <3",
                    "What? You don't care about her?",
                    "Fine. Fine.",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "No hints for you. Can't you read?",
                    "Okay. I see you have determination.",
                    "Okay. I see you have determination.",
                    "I said it twice",
                    "because I knew you press fast.",
                    "I will give you one more hint.",
                    "Just one, no more no less.",
                    "ONE. LAST. HINT.",
                    "Now, this one is quite boring too.",
                    "You might have known it anyway.",
                    "Huh? You still want to know?",
                    "You realise this is going nowhere right?",
                    "Alright. Alright.",
                    "If you want to have a rest during a game",
                    "Press 'P'",
                    "Only works in Single mode",
                    "That's it.",
                    "I told you it's boring.",
                    "I'm getting tired of you. That's it.",
                    "Have a good time playing the game!",
                    ""]

    def change_troll(self):
        self.troll_c  = min(self.troll_c + 1, len(self.msgs) - 1)
        msg = self.msgs[self.troll_c]
        self.hints.set_text(msg)
        self.hints.position_mid(SCREEN_WIDTH/2 + 280, SCREEN_HEIGHT/2 + 210)
        if self.troll_c < len(self.msgs) - 1:
            self.troll_snd.play(0)


    def render(self, screen):
        # Render image
        screen.blit(self.image, (self.rect))
        # Render text
        self.username.render(screen)
        # Render button
        for i in reversed(self.buttons):
            i.render(screen)
        if self.troll:
            self.hints.render(screen)

    def event_unblocking(self, keys): # Continuously detecting events
        if keys[K_BACKSPACE]:
            self.username.text = self.username.text[:-1]

    def event_blocking(self, event):
        self.change_button_state(event)
        return self.enter_name(event)

    def change_button_state(self, event):
        if event.key == K_LEFT :
            self.buttons[self.state].toggle()
            self.state = mod((self.state - 1) % 3)
            self.buttons[self.state].toggle()
            self.troll = False
            self.sound.play(0)
        elif event.key == K_RIGHT or event.key == K_TAB:
            self.buttons[self.state].toggle()
            self.state = (self.state + 1) % 3
            self.buttons[self.state].toggle()
            self.troll = False
            self.sound.play(0)

    ''' User entering data, returns true if user enters K_RETURN '''
    def enter_name(self, event):
        if self.username.get_size()[0] < 350 and (event.unicode.isalpha() or event.unicode == ' '):
            self.username.addchar(event.unicode)
        if event.key == K_RETURN:
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
        position_centre(self.image, self.rect)

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
        self.text = 'HP'
        self.hp_text = self.font.render(self.text, True, self.blood_color)
        self.rect_white = [SCREEN_WIDTH - 200, 15, 150, 32]

    def position(self, x, y):
        self.rect_white[0] = x
        self.rect_white[1] = y

    def render(self, screen):
        screen.blit(self.hp_text, (self.rect_white[0] - 50, self.rect_white[1] - 5))
        pygame.draw.rect(screen, (255,255,255), self.rect_white)
        if self.hp > 0:
            rect_blood = (self.rect_white[0], self.rect_white[1], self.hp * 15, 32)
            pygame.draw.rect(screen, self.blood_color, rect_blood)
    def change_hp(self, offset):
        hp = self.hp + offset
        if hp > 10:
            self.hp = 10
        else:
            self.hp = hp if hp >= 0 else 0


class Scorepad(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        # Initialize font
        self.font = pygame.font.Font(FONT, 32)
        self.score = 0
        self.pos = (50,10)
        self.right = False

    def position(self, x, y):
        self.pos =(x,y)

    def render(self, screen):
        string = "Score: " + str(self.score)
        scorepad = self.font.render(string, True, (95,92,119))
        if self.right: # Scorepad is at the right cornet
            pos = (self.pos[0] - scorepad.get_width(), self.pos[1])
            screen.blit(scorepad, pos)
        else:
            screen.blit(scorepad, self.pos)
    def change_score(self, offset):
        score = self.score + offset
        if score <= 0:
            self.score = 0
        elif score > 1 << 16:
            self.score = 1 << 16 - 1 # You crazy
        else:
            self.score = score

class Egg(pygame.sprite.Sprite):
    def __init__(self, filename, width=None, height=None, drop_vel=10, seed=-1):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image(filename, width=width, height=height)
        self.x = position_rand_top(self.image, self.rect, seed=seed)
        self.y = 0
        self.y_dist = drop_vel

    def drop(self):
        self.rect.move_ip(0, self.y_dist)
        self.y += self.y_dist

    def render(self, screen):
        screen.blit(self.image, (self.rect))


class StoneEgg(Egg):
    def __init__(self, seeds=(-1,-1)):
        super().__init__('stone_egg_40.png', height=60, drop_vel=randint(10,15,seed=seeds[0]), seed=seeds[1])

class GoldEgg(Egg):
    def __init__(self, seeds=(-1,-1)):
        super().__init__('gold_egg_30.png', height=35, drop_vel=randint(3,10, seed=seeds[0]), seed=seeds[1])


class Backdrop(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('backdrop_1080.jpg', width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.vel_x = 0
        self.vel_y = 0

    def render(self, screen):
        screen.blit(self.image, (self.rect))

class Chicken(pygame.sprite.Sprite):
    ''' opp: load opponent chicken image file '''
    def __init__(self, chick=0, opp=False):
        pygame.sprite.Sprite.__init__(self)
        if opp: # Load opponent chicken sprite
            self.image, self.rect = load_image('chick%d_opp_120.png' % chick, width=120, height=120)
        else:
            self.image, self.rect = load_image('chick%d_120.png' % chick, width=120, height=120)
        self.dead_image = load_image('chicken_dead_120.png',width=120, height=120)[0]
        # Set the number of pixels to move each time
        self.x_dist = 10
        self.x, self.y = 0, 0
        # Place chicken at the bottom center of the page
        self.position(SCREEN_WIDTH/2, SCREEN_HEIGHT - 180)
        self.dead = False
        self.opp = opp
        self.id = chick

    def set_chickid(self,chickid):
        if self.opp: # Load opponent chicken sprite
            self.image = load_image('chick%d_opp_120.png' % chickid, width=120, height=120)[0]
        else:
            self.image = load_image('chick%d_120.png' % chickid, width=120, height=120)[0]
        self.id = chickid

    def get_chickid(self):
        return self.id

    ''' Place sprite at exactly the coordinates specified '''
    def position(self, x, y=SCREEN_HEIGHT - 200):
        self.rect.move_ip(x - self.x, y - self.y)
        self.x, self.y = x, y

    ''' Key is the pygame define for either left/right '''
    def move(self, keys):
        if not self.dead:
            xMove = 0
            if ((keys[K_RIGHT] or keys[K_d]) and self.x < SCREEN_WIDTH - self.image.get_size()[0]):
                xMove = self.x_dist
                self.x += self.x_dist
            elif ((keys[K_LEFT] or keys[K_a]) and self.x > 0):
                xMove = -self.x_dist
                self.x -= self.x_dist
            self.rect.move_ip(xMove, 0)

    def render(self, screen):
        if not self.dead:
            screen.blit(self.image, (self.rect))
        else:
            screen.blit(self.dead_image, (self.rect))

class Button(pygame.sprite.Sprite):
    def __init__(self, name, pos, width=None, height=None, selected=False):
        self.image, self.rect = load_image(name + '.png', width=width, height=height)
        self.image_selected, self.rect_selected = load_image(name + '_selected.png', width=width, height=height)
        self.selected = selected
        position_mid(self.image, self.rect, pos[0], pos[1])
        position_mid(self.image_selected, self.rect_selected, pos[0], pos[1])

    def toggle(self):
        self.selected = not self.selected

    def render(self, screen):
        if self.selected:
            screen.blit(self.image_selected, (self.rect_selected))
        else:
            screen.blit(self.image, (self.rect))
    def get_rect(self):
        return self.rect

class TextBox(pygame.sprite.Sprite):
    def __init__(self, filename=None, width=None, height=None, fontsize=30, fontcolor=(0,0,0), blinker=False):
        self.image, self.rect = None, None
        if filename:
            self.image, self.rect = load_image(filename, width=width, height=height)
        self.text = ""
        self.text_pos = (0,0)
        self.fontcolor = fontcolor # Default to black
        self.font = pygame.font.Font(FONT, fontsize)
        self.blinker_state = blinker
        self.blinker = pygame.Surface((fontsize/2, fontsize))
        self.blinker.fill(fontcolor)
        self.blinker_counter = 0
        self.blinker_duration = 35
        # Render text
        self.text_render = self.font.render(self.text, True, self.fontcolor)

    def get_size(self):
        self.text_render = self.font.render(self.text, True, self.fontcolor)
        return self.text_render.get_size()

    def addchar(self, char):
        self.text += char
        self.text_render = self.font.render(self.text, True, self.fontcolor)

    def toggle_blinker(self):
        self.blinker_state = not self.blinker_state

    def set_fontsize(self, fontsize):
        self.font = pygame.font.Font(FONT, fontsize)

    def set_fontcolor(self, color):
        self.fontcolor = color

    def set_text(self, text):
        self.text = text
        self.text_render = self.font.render(self.text, True, self.fontcolor)

    def render(self, screen):
        screen.blit(self.text_render, self.text_pos)
        # Render blinker
        if self.blinker_state:
            if self.blinker_counter < self.blinker_duration/2:
                # Position blinker after text
                blinker_pos = (self.text_pos[0] + self.text_render.get_width(), self.text_pos[1] + 3)
                screen.blit(self.blinker, (blinker_pos))
            if self.blinker_counter < self.blinker_duration:
                self.blinker_counter += 1
            else:
                self.blinker_counter = 0
        # Render background image
        if self.image:
            screen.blit(self.image, self.rect)

    def position_left(self, x, y): # by left-point
        if self.image:
            position_left(self.image, self.rect, x - 10, y)
        self.text_pos = (x,y)

    def position_mid(self, x, y): # by mid-point
        if self.image:
            position_centre(self.image, self.rect, x, y)
        self.text_pos = (x - self.text_render.get_width()/2, y)


class MultiConfigBackdrop(pygame.sprite.Sprite):
    def __init__(self, image):
        self.image, self.rect = load_image(image)
        position_centre(self.image, self.rect)
    def render(self, screen):
        screen.blit(self.image, (self.rect))

class MulticonfigHostOrConn(pygame.sprite.Sprite):
    def __init__(self, sound):
        self.backdrop = MultiConfigBackdrop('multiconfig_0.png')
        self.sound = sound
        # Host/Connection Buttons
        pos = (SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT/2)
        host = Button('host', pos, width=(SCREEN_WIDTH/3 + 20), selected=True)
        pos = (SCREEN_WIDTH/2 + 200, SCREEN_HEIGHT/2)
        connect = Button('connect', pos, width=(SCREEN_WIDTH/3 + 20), selected=False)
        self.buttons = [host, connect]
        self.host = True
    def render(self, screen):
        self.backdrop.render(screen)
        for i in self.buttons:
            i.render(screen)
    def keyevent(self, event):
        if event.key in [K_TAB, K_LEFT, K_RIGHT]:
            self.buttons[0].toggle()
            self.buttons[1].toggle()
            self.host = not self.host
            self.sound.play(0)

class MultiConfigIPPort(pygame.sprite.Sprite):
    def __init__(self):
        self.backdrop = MultiConfigBackdrop('multiconfig_1.png')
        # Initialize and position textboxes
        ip = TextBox(fontcolor=(255,255,255), fontsize=40, blinker=True)
        ip.position_left(SCREEN_WIDTH/2 - 350, SCREEN_HEIGHT/2 - 60)
        port = TextBox(fontcolor=(255,255,255), fontsize=40)
        port.position_left(SCREEN_WIDTH/2 + 170, SCREEN_HEIGHT/2 - 60)
        self.text = [ip, port]
        self.currtext = 0
        self.error = None
        self.loading = False

    def render(self, screen):
        self.backdrop.render(screen)
        for i in self.text:
            i.render(screen)
        if self.error:
            self.error.render(screen)

    def set_error(self, errormsg):
        self.error = TextBox(fontcolor=(31,50,84),fontsize=20)
        self.error.set_text(errormsg)
        self.error.position_left(SCREEN_WIDTH/2 - 350, SCREEN_HEIGHT/2 + 20)

    def keyevent(self, event):
        if event.key in [K_TAB, K_RIGHT, K_LEFT]:
            self.error = None
            self.text[0].toggle_blinker()
            self.text[1].toggle_blinker()
            self.currtext = (self.currtext + 1) % 2
        elif event.unicode.isdigit():
            self.error = None
            if self.currtext == 0: # Modifying IP
                if len(self.text[0].text) > 14:
                    return # Don't do anything
                self.text[0].addchar(event.unicode)
            else: # Modifying port
                if len(self.text[1].text) > 4:
                    return
                self.text[1].addchar(event.unicode)
        elif event.key == K_PERIOD and self.currtext == 0:
            self.error = None
            if len(self.text[0].text) > 14:
                return # Don't do anything
            self.text[0].addchar('.')
        elif event.key == K_BACKSPACE:
            self.error = None
            curr = self.currtext
            self.text[curr].set_text(self.text[curr].text[:-1])


class MultiConfigChooseChick(pygame.sprite.Sprite):
    def __init__(self, sound):
        self.backdrop = MultiConfigBackdrop('multiconfig_2.png')
        # Chicken Buttons
        self.chicken = 0 # Select the first chicken by default
        pos = (SCREEN_WIDTH/2 - 300, SCREEN_HEIGHT/2 + 80)
        chick0 = Button('chick0_slot', pos, width=200, selected=True)
        pos = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 80)
        chick1 = Button('chick1_slot', pos, width=200)
        pos = (SCREEN_WIDTH/2 + 300, SCREEN_HEIGHT/2 + 80)
        chick2 = Button('chick2_slot', pos, width=200)
        self.chickens = [chick0, chick1, chick2]
        self.sound = sound
    def render(self, screen):
        self.backdrop.render(screen)
        for i in self.chickens:
            i.render(screen)
    def keyevent(self, event):
        if event.key == K_LEFT:
            self.chickens[self.chicken].toggle()
            self.chicken = mod((self.chicken - 1) % 3)
            self.chickens[self.chicken].toggle()
            self.sound.play(0)
        if event.key == K_TAB or event.key == K_RIGHT:
            self.chickens[self.chicken].toggle()
            self.chicken = (self.chicken + 1) % 3
            self.chickens[self.chicken].toggle()
            self.sound.play(0)


class MultiConfigScreen(pygame.sprite.Sprite):
    def __init__(self, sound):
        self.state = 0
        s0 = MulticonfigHostOrConn(sound)
        s1 = MultiConfigIPPort()
        s2 = MultiConfigChooseChick(sound)
        self.screens = [s0, s1, s2]

    def render(self, screen):
        self.screens[self.state].render(screen)

    def keyevent(self, event, screen):
        if event.key == K_ESCAPE and self.state == 0: # Back to StartScreen
            return -1
        elif event.key == K_ESCAPE: # Revert step
            if self.state == 1: # Clear error messages
                self.screens[1].set_error('')
            self.state -= 1
        elif event.key == K_RETURN and self.state == 2: # Proceed to connection
            return 1
        elif event.key == K_RETURN: # Proceed to next step in multiconfig
            if self.state == 1: # Entering IP/Port
                # Check if the IP/PORT is correct and available
                error = None
                try:
                    if len(self.get_ip()) == 0:
                        raise ValueError
                    if self.is_host():
                        tmp = socketserver.UDPServer((self.get_ip(), self.get_port()), socketserver.BaseRequestHandler)
                        tmp.server_close()
                    else:
                        tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        tmp.settimeout(0.5)
                        count = 0
                        recv = [-1]
                        self.screens[1].set_error('Checking if the server is alive...')
                        while not recv[0] == 0:
                            count += 1
                            tmp.sendto(bytes([0]), (self.get_ip(), self.get_port()))
                            try:
                                recv = tmp.recv(1)
                                self.screens[1].set_error('')
                            except socket.timeout:
                                if count > 10:
                                    raise socket.timeout
                                self.screens[1].render(screen)
                                pygame.display.update()
                                pygame.event.pump()
                                continue
                            tmp.close()
                except socket.timeout:
                    error = 'Connection Timeout'
                except socket.gaierror:
                    error = 'Invalid host IP'
                except OSError:
                    error = 'Can\'t assign requested address'
                except PermissionError:
                    error = 'Permission denied'
                except OverflowError:
                    error = 'Port must be 0-65535'
                except UnicodeError:
                    error = "Are you a chicken?"
                except ValueError:
                    error = 'Please enter host IP and port'
                except:
                    error = 'Unknown error occurred'
                finally:
                    if error:
                        self.screens[1].set_error(error)
                        return 0

            self.state += 1
        else: # Let the screens decide what to do
            self.screens[self.state].keyevent(event)
        return 0 # No action
    def is_host(self):
        return self.screens[0].host
    def get_ip(self):
        return self.screens[1].text[0].text
    def get_port(self):
        return int(self.screens[1].text[1].text)
    def get_chickid(self):
        return self.screens[2].chicken

class ConnectingScreen(pygame.sprite.Sprite):
    def __init__(self):
        self.image, self.rect = load_image('connecting.png')
        position_centre(self.image, self.rect)
        self.text = TextBox(fontsize=20, fontcolor=(218,180,81))
        self.set_text('Connecting...')
    def set_text(self, text):
        self.text.set_text(text)
        self.text.position_mid(SCREEN_WIDTH/2, SCREEN_HEIGHT/2+80)
    def render(self, screen):
        screen.blit(self.image, (self.rect))
        self.text.render(screen)

class WinLossScreen(pygame.sprite.Sprite):
    def __init__(self, score, opp_score):
        winner = 0
        if score > opp_score:
            winner = 1
        elif score < opp_score:
            winner = -1

        self.bg_image, self.bg_rect = load_image('win_loss_screen.png', width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.banner = TextBox(fontsize=80, fontcolor=(255,255,255))
        self.winner = TextBox(fontsize=40, fontcolor=(255,255,255))
        self.loser = TextBox(fontsize=20, fontcolor=(255,255,255))
        msg, lose, win = '', '', ''
        if winner == 1:
            msg = 'YOU WON'
            win = 'You scored %d points' % score
            lose = 'They scored %d points' % opp_score
        elif winner == 0:
            msg = 'DRAW'
            win = 'You both scored %d points' % score
        else:
            msg = 'YOU LOST'
            win = 'They scored %d points' % opp_score
            lose = 'You scored %d points' % score
        # set textboxes text
        self.banner.set_text(msg)
        self.winner.set_text(win)
        self.loser.set_text(lose)
        # Position textboxes
        self.banner.position_mid(SCREEN_WIDTH/2, 100)
        self.winner.position_mid(SCREEN_WIDTH/2 - 30, SCREEN_HEIGHT/2 + 150)
        self.loser.position_mid(SCREEN_WIDTH-150, SCREEN_HEIGHT/2 + 20)

    def render(self, screen):
        screen.blit(self.bg_image, self.bg_rect)
        self.banner.render(screen)
        self.winner.render(screen)
        self.loser.render(screen)
