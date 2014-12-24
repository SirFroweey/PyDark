import logging
import threading
import base64
import pygame
import Queue
import time
import icon
import sys
import net
import os
import ui
# pygame
from pygame.locals import *
# xml processing
from xml import sax



screen_hwnd = None


##########################################
# Resources: Twisted, pygnetic and tiled #
##########################################
# http://usingpython.com/pygame-tilemaps/
# http://bazaar.launchpad.net/~game-hackers/game/trunk/view/head:/gam3/network.py
# http://pygnetic.readthedocs.org/en/latest/api/index.html#module-pygnetic.client


class DataQueue(object):
    """
    A DataQueue can be used to share data between DarkThreads and your game.
    """
    def __init__(self, max_items=100):
        self.max_items = max_items
        self.q = Queue.Queue(self.max_items)
    def add(self, data):
        self.q.put(data)
    def remove(self, data):
        pass
    def exists(self, key):
        pass


class Player(object):
    """PyDark network and/or local player."""
    def __init__(self, network=None, name=None, **kwargs):
        self.kwargs = kwargs
        self.name = name
        self.net = network
        self.sprite = None
        self.controllable = False # Let's PyDark Game() instance know \
        # if we can control this player. Server also verifies this if \
        # this is a network(multiplayer) game.
    def SetSprite(self, sprite_instance):
        self.sprite = sprite_instance
    def SetControl(self, boolean):
        self.controllable = boolean
    def __repr__(self):
        if self.net is not None:
            return "Player: <%s>" %self.net.transport.getPeer()
        else:
            return "Player: <%s>" %self.name


class Block(object):
    """Terrain object that can optionally be created, moved, or destroyed."""
    def __init__(self, name, image, size):
        self.name = name
        self.img = img


class World(object):
    """World that holds all other objects. Size of world is determined /
       by size[0] * size[1] worth of Land() instances."""
    def __init__(self, name="World 1", size=(30, 30)):
        self.name = name
        self.width = size[0]
        self.height = size[1]


class Camera(object):
    """Object that controlls which Block() instances should be displayed /
       along with all other objects, including Player() instances."""
    def __init__(self, x, y):
        self.x = x
        self.y = y


class TileSet(object):
    def __init__(self, file, tile_width, tile_height):
        image = pygame.image.load(file).convert_alpha()
        if not image:
            print "Error creating new TileSet: file %s not found" % file
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.tiles = []
        for line in xrange(image.get_height()/self.tile_height):
            for column in xrange(image.get_width()/self.tile_width):
                pos = Rect(
                        column*self.tile_width,
                        line*self.tile_height,
                        self.tile_width,
                        self.tile_height )
                self.tiles.append(image.subsurface(pos))
 
    def get_tile(self, gid):
        return self.tiles[gid]


class TMXHandler(sax.ContentHandler):
    def __init__(self):
        self.width = 0
        self.height = 0
        self.tile_width = 0
        self.tile_height = 0
        self.columns = 0
        self.lines  = 0
        self.properties = {}
        self.image = None
        self.tileset = None
 
    def startElement(self, name, attrs):
        # get most general map informations and create a surface
        if name == 'map':
            self.columns = int(attrs.get('width', None))
            self.lines  = int(attrs.get('height', None))
            self.tile_width = int(attrs.get('tilewidth', None))
            self.tile_height = int(attrs.get('tileheight', None))
            self.width = self.columns * self.tile_width
            self.height = self.lines * self.tile_height
            self.image = pygame.Surface([self.width, self.height]).convert()
        # create a tileset
        elif name=="image":
            source = attrs.get('source', None)
            self.tileset = TileSet(source, self.tile_width, self.tile_height)
        # store additional properties.
        elif name == 'property':
            self.properties[attrs.get('name', None)] = attrs.get('value', None)
        # starting counting
        elif name == 'layer':
            self.line = 0
            self.column = 0
        # get information of each tile and put on the surface using the tileset
        elif name == 'tile':
            gid = int(attrs.get('gid', None)) - 1
            if gid <0: gid = 0
            tile = self.tileset.get_tile(gid)
            pos = (self.column*self.tile_width, self.line*self.tile_height)
            self.image.blit(tile, pos)
 
            self.column += 1
            if(self.column>=self.columns):
                self.column = 0
                self.line += 1
 
    # just for debugging
    def endDocument(self):
        pass
        #print self.width, self.height, self.tile_width, self.tile_height
        #print self.properties
        #print self.image


class Map(object):
    """
    PyDark map instance. Load's a Tiled(.tmx) map into memory and \
    returns a pygame.Surface object.
    """
    def __init__(self, fileName, position=(0,0)):
        self.parser = sax.make_parser()
        self.tmxhandler = TMXHandler()
        self.filename = fileName
        self.position = position
    def load(self):
        self.parser.setContentHandler(self.tmxhandler)
        self.parser.parse(self.filename)
    def Update(self):
        pass
    def Draw(self):
        pass
        

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


class DarkSprite(pygame.sprite.Sprite):
    def __init__(self, name, starting_position=None, sprite_list=None,
                 sprite_sheet=None):
        """Base PyDark 2D sprite. Takes 3 arguments: (name, starting_position, sprite_list)"""
        pygame.sprite.Sprite.__init__(self)
        self.name = name
        self.index = 0
        self.subsprites = None
        if sprite_list:
            self.subsprites = sprite_list
        elif sprite_sheet:
            self.subsprites = sprite_sheet
        self.starting_position = starting_position
    def Draw(self, surface=None):
        if surface:
            surface.blit(self.image, self.rect)
        else:
            self.surface.blit(self.image, self.rect)
    def LoadContent(self, filename, alpha=True):
        if alpha:
            self.image = pygame.image.load(filename).convert_alpha()
        else:
            self.image = pygame.image.load(filename).convert()
        self.rect = self.image.get_rect()
    def Update(self):
        pass
    def Collision(self, other):
        pass
    def SetPosition(self, position=None):
        if position:
            self.rect.topleft = position
        else:
            self.rect.topleft = self.starting_position


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
        # list of players(network or local) to drawn onto our Scene()
        self.players = []
        # handle to our pygame surface(can be window or overlay)
        self.surface = surface
        #
        self.name = name
        #
        self.map = None
    def window_size(self):
        return self.surface.screen.get_size()
    def add_object(self, obj):
        self.objects.append(obj)
    def add_player(self, player_instance):
        self.players.append(player_instance)
    def remove_object(self, obj):
        self.objects.remove(obj)
    def Draw(self, item=None):
        """Draw all self.objects onto our Scene() view."""
        if item is None:
            for item in self.objects:
                # Handle drawing our map
                if isinstance(item, Map):
                    pos = item.position
                    self.surface.screen.blit(item.tmxhandler.image, pos)
                # Handle drawing sprites
                elif isinstance(item, DarkSprite):
                    pass
                # Handle drawing UI overlay
                elif isinstance(item, ui.Overlay):
                    pos = item.position
                    #self.Update(item)
                    item.Draw()
                    self.surface.screen.blit(item.panel, pos)
        else:
            # Handle drawing our Map
            if isinstance(item, Map):
                pos = item.position
                self.surface.screen.blit(item.tmxhandler.image, pos)
            # Handle drawing sprites
            elif isinstance(item, DarkSprite):
                pass
            # Handle drawing UI Overlay
            elif isinstance(item, ui.Overlay):
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
    def LoadMap(self, map_instance):
        self.map = map_instance
        print "Set self.map:", self.map
    def __repr__(self):
        return "<PyDark.engine.Scene: {0}>".format(self.name)
            

class Game(object):
    def __init__(self, title, window_size, icon=None,
                 center_window=True, FPS=30, online=False,
                 server_ip=None, server_port=None):
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
        # if game uses online features
        self.online = online
        self.server_ip = server_ip
        self.server_port = server_port
        self.connection = None
        if online:
            if server_ip and server_port:
                self.create_online_connection()
            else:
                raise ValueError, "You must pass server_ip and server_port to your Game() instance"
        # start pygame display
        self.initialize()
    def create_online_connection(self):
        try:
            self.connection = self.client.connect(self.server_ip, self.server_port)
        except:
            # could not connect to server
            self.connection = None
    def initialize(self):
        pygame.init()
        pygame.mixer.init()
        pygame.font.init()
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

        if self.connection:
            # Handling network messages
            if event.type == pygnetic.event.NETWORK and event.connection == self.connection:
                if event.net_type == pygnetic.event.NET_CONNECTED:
                    print "Connected"
                elif event.net_type == pygnetic.event.NET_DISCONNECTED:
                    print "Disconnected"
                elif event.net_type == pygnetic.event.NET_RECEIVED:
                    if event.msg_type == self.chat_msg:
                        msg = event.message.msg
                        print msg
            
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
        #try:
        #    filename = filename.replace("/", "\\")
        #    filename = os.path.join(os.getcwd(), filename)
        self.sheet = pygame.image.load(filename).convert()
        self.width = self.sheet.get_size()[0]
        self.height = self.sheet.get_size()[1]
        self.filename = filename
        #except pygame.error, message:
        #    print 'Unable to load spritesheet image:', filename
        #    raise SystemExit, message
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
    def __repr__(self):
        return "<PyDark.engine.SpriteSheet({0} x {1}): {2}>".format(
            self.width,
            self.height,
            self.filename,
            )


    #ss = spritesheet.spriteshee('somespritesheet.png')
    # Sprite is 16x16 pixels at location 0,0 in the file...
    #image = ss.image_at((0, 0, 16, 16))
    #images = []
    # Load two images into an array, their transparent bit is (255, 255, 255)
    #images = ss.images_at((0, 0, 16, 16),(17, 0, 16,16), colorkey=(255, 255, 255))


    

