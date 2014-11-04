import threading
import base64
import pygame
import time
import icon
import sys
import os
import ui
#
from pygame.locals import *


screen_hwnd = None
    

def Color(r, g, b, a):
    return pygame.Color(r, g, b, a)


def convert_image_to_string(img):
    return pygame.image.tostring(img, 'RGBA')


def write_hdd(fileName, data):
    f = file(fileName, "w")
    f.write(base64.b64encode(data))
    f.close()


def read_hdd(fileName):
    f = file(fileName, "r")
    d = base64.b64decode(f.read())
    f.close()
    return d


def get_image_file(img):
    return pygame.image.load(img).convert_alpha()


def seticon(iconname):
    pygame.display.set_icon(pygame.image.load(iconname))


class BaseSprite(pygame.sprite.Sprite):
    def __init__(self, name, text=None, position=(0, 0), image_sprites=None):
        pygame.sprite.Sprite.__init__(self)
        self.image_sprite = image_sprites
        self.position = position
        self.text = text
        self.name = name
        if self.text:
            self.initFont()
        self.initImage()
        self.initGroup()
        if self.text:
            self.setText()

    def initFont(self):
        pygame.font.init()
        self.font = pygame.font.Font(None,3)

    def initImage(self):
        if not self.image_sprite:
            self.image = pygame.Surface((200,80))
            self.image.fill((255,255,255))
        else:
            self.image = pygame.image.load(self.image_sprite).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = self.position       

    def setText(self):
        tmp = pygame.display.get_surface()
        x_pos = self.rect.left+5
        y_pos = self.rect.top+5

        x = self.font.render(self.text,False,(0,0,0))
        tmp.blit(x,(x_pos,y_pos))


    def Update(self, mouseCoords=None, clickEvent=False, hoverEvent=False):
        pass

    def initGroup(self):
        self.group = pygame.sprite.GroupSingle()
        self.group.add(self)


class DarkThread(threading.Thread):
    def __init__(self, name, func, runafter=None, params=[]):
        threading.Thread.__init__(self)
        self.daemon = True
        self.runafter = runafter
        self.params = params
        self.name = name
        self.func = func
    def run(self):
        if self.runafter:
            time.sleep(self.runafter)
        self.func(self.params)
    

class Object(object):
    """A sprite, texture, or any UI element used by our game."""
    # Objects keeps our data handy, like the position to draw the Object,
    # and its alive-time(if any).
    def __init__(self, image):
        pass
    

class Scene(object):
    """A scene is a presentation of objects and UI elements."""
    def __init__(self, surface, name):
        # wether or not we should "draw" or "display" this scene
        self.display = True
        # list of objects to draw onto our Scene()
        self.objects = []
        # handle to our pygame surface(can be window or overlay)
        self.surface = surface
        #
        self.name = name
    def window_size(self):
        return self.surface.screen.get_size()
    def add_object(self, obj):
        self.objects.append(obj)
    def remove_object(self, obj):
        self.objects.remove(obj)
    def Draw(self, item=None):
        """Draw all self.objects onto our Scene() view."""
        if item is None:
            for item in self.objects:
                pos = item.position
                #self.Update(item)
                item.Draw()
                self.surface.screen.blit(item.panel, pos)
        else:
            #self.Update(item)
            item.Draw()
            pos = item.position
            self.surface.screen.blit(item.panel, pos)
    def Update(self, item=None):
        """Update all our self.objects on our Scene() view."""
        if item is None:
            for item in self.objects:
                item.Update()
        else:
            item.Update()
    def __repr__(self):
        return "<PyDark.engine.Scene: {0}>".format(self.name)
            

class Game(object):
    def __init__(self, title, window_size, icon=None,
                 center_window=True, FPS=30):
        self.clock = pygame.time.Clock()
        self.FPS = FPS
        self.elapsed = 0
        # Window title for our Game
        self.title = title
        # Window size for our Game
        self.size = window_size
        # Window icon for our Game
        self.icon = icon
        # let's us know if our game should be running(boolean)
        self.running = True
        # list of "scenes"
        self.scenes = dict()
        # current "scene" to display on screen
        self.currentScene = None
        # default backgroundColor
        self.backgroundColor = (0, 0, 0)
        # wether or not we should center of our games window
        if center_window is True:
            ui.center_window()
        # start pygame display
        self.initialize()
    def initialize(self):
        pygame.init()
        pygame.mixer.init()
        # set icon(if supplied)
        if self.icon is not None:
            seticon(self.icon)
            # set window caption(title) and icon
            pygame.display.set_caption(self.title, self.icon)
        else:
            # set default icon
            rgb = base64.b64decode(icon.get_default_icon())
            pygame.display.set_icon(pygame.image.fromstring(rgb, (128, 128), 'RGBA'))
            # set window caption(title)
            pygame.display.set_caption(self.title)
        # handle to our screen buffer
        global screen_hwnd
        self.screen = pygame.display.set_mode(self.size, pygame.DOUBLEBUF)
        screen_hwnd = self.screen
        #write_hdd("icon.txt", convert_image_to_string(get_image_file("PyDark/preferences_desktop_gaming.png")) )
    def add_scene(self, _scene):
        self.scenes[_scene.name] = _scene
    def start(self):
        if len(list(self.scenes)) > 0:
            self.mainloop()
        else:
            raise ValueError, "You must supply at least one-scene."
    def processEvent(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.update_scene_objects(clickEvent=True)
        elif event.type == pygame.MOUSEMOTION:
            self.update_scene_objects(hoverEvent=True)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.constants.K_BACKSPACE:
                char = pygame.constants.K_BACKSPACE
            else:
                char = event.unicode
            self.update_scene_objects(keyEvent=True, keyChar=char)
    def update_scene_objects(self, clickEvent=False, hoverEvent=False, keyEvent=False,
                             keyChar=None):
        pos = pygame.mouse.get_pos()
        this_scene = self.get_current_scene()
        for item in this_scene.objects:
            if isinstance(item, ui.Overlay):
                # This item is an Overlay /
                # iterate through all its self.drawables.
                self.handle_overlay_objects(
                    pos,
                    item,
                    clickEvent,
                    hoverEvent,
                    keyEvent,
                    keyChar
                )
    def handle_overlay_objects(self, pos, item, clickEvent, hoverEvent, keyEvent,
                               keyChar):
        for e in item.drawables.keys():
            obj = item.drawables.get(e)
            if clickEvent:
                obj.Update(pos, clickEvent=True)
            elif hoverEvent:
                obj.Update(pos, hoverEvent=True)
            elif keyEvent:
                # if object is a textbox, check if it is focused.
                # if so, enter text.
                if isinstance(obj, ui.TextBox):
                    if obj.focused:
                        # if backspace is pressed, delete a character.
                        if keyChar == pygame.constants.K_BACKSPACE:
                            obj.text = obj.text[:-1]
                        else:
                            # otherwise, populate text entry with new character.
                            obj.text += keyChar
                        obj.set_text()
    def draw_current_scene(self):
        value = self.scenes.get(self.currentScene)
        value.Draw()
    def get_current_scene(self):
        return self.scenes.get(self.currentScene)
    def Update(self):
        if self.currentScene is not None:
            this_scene = self.get_current_scene()
            this_scene.Update()
    def Draw(self):
        self.screen.fill(self.backgroundColor)
        if self.currentScene is not None:
            self.draw_current_scene()
        pygame.display.update()
        self.screen.fill((0, 0, 0))
    def Load(self, content):
        pass
    def Unload(self, content):
        pass
    def mainloop(self):
        while self.running:
            for event in pygame.event.get():
                self.processEvent(event)

            self.Update()
            self.Draw()
            self.elapsed = self.clock.tick(self.FPS)
                
        pygame.mixer.quit()
        pygame.quit ()
        sys.exit()
    

class SpriteSheet(object):
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error, message:
            print 'Unable to load spritesheet image:', filename
            raise SystemExit, message
    # Load a specific image from a specific rectangle
    def image_at(self, rectangle, colorkey = None):
        "Loads image from x,y,x+offset,y+offset"
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image
    # Load a whole bunch of images and return them as a list
    def images_at(self, rects, colorkey = None):
        "Loads multiple images, supply a list of coordinates" 
        return [self.image_at(rect, colorkey) for rect in rects]
    # Load a whole strip of images
    def load_strip(self, rect, image_count, colorkey = None):
        "Loads a strip of images and returns them as a list"
        tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)


    #ss = spritesheet.spriteshee('somespritesheet.png')
    # Sprite is 16x16 pixels at location 0,0 in the file...
    #image = ss.image_at((0, 0, 16, 16))
    #images = []
    # Load two images into an array, their transparent bit is (255, 255, 255)
    #images = ss.images_at((0, 0, 16, 16),(17, 0, 16,16), colorkey=(255, 255, 255))


    

