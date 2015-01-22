import logging
import threading
import vector2d
import base64
import pygame
import Image
import Queue
import math
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


# Left off: Need to keep track of which keys are being pressed down and store them as boolean values \
# so I can determine when the client has released those keys. This way client players can move by holding \
# left, right, up or down.

# Left off: Finish Player() class.
# Created RegisterKeyPress() and RegisterMousePress() functions to specify function callbacks when given keys are pressed.


screen_hwnd = None
game_instance = None


##########################################
# Resources: PyGame, Twisted and Tiled #
##########################################
# http://usingpython.com/pygame-tilemaps/
# http://bazaar.launchpad.net/~game-hackers/game/trunk/view/head:/gam3/network.py
# http://pygnetic.readthedocs.org/en/latest/api/index.html#module-pygnetic.client


def pygame_to_pil_img(pg_surface):
    imgstr = pygame.image.tostring(pg_surface, 'RGB')
    return Image.fromstring('RGB', pg_surface.get_size(), imgstr)


def font(name, size):
    return pygame.font.SysFont(name, size)


def Hexagon(Radius, SCREENX, SCREENY, Side=0):
    # Moar Crazy Math, returns co-ords for a single side of the Hexagon
    a = int(math.sin(math.radians(30)) * (Radius / math.sin(math.radians(60))))
    x = SCREENX / 2; y = SCREENY / 2; r = Radius
    if Side == 0: return [(x + r,y + a), (x + r,y - a), (x,y - 2 * a), (x - r,y - a), (x - r,y + a), (x,y + 2 * a)]
    if Side == 1: return [(x + r,y + a), (x + r,y - a)]
    if Side == 2: return [(x + r,y - a), (x,y - 2 * a)]
    if Side == 3: return [(x,y - 2 * a), (x - r,y - a)]
    if Side == 4: return [(x - r,y - a), (x - r,y + a)]
    if Side == 5: return [(x - r,y + a), (x,y + 2 * a)]
    if Side == 6: return [(x,y + 2 * a), (x + r,y + a)]


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
    """PyDark network and/or local player instance."""
    def __init__(self, network=None, name=None, xspeed=1, yspeed=1, **kwargs):
        self.kwargs = kwargs
        self.xspeed = xspeed # player x-coordinate speed(in pixels)
        self.yspeed = yspeed # player y-coordinate speed(in pixels)
        self.name = name
        self.net = network
        self.key_pressed_dict = {} # dictionary containing keyboard_character, function_handle pairs.
        self.key_held_dict = {} # dictionary containing keyboard_character, function_handle pairs.
        self.mouse_dict = {} # dictionary containing mouse_button, function_handle pairs.
        self.sprite = None
        self.controllable = False # Let's PyDark Game() instance know \
        # if we can control this player. Server also verifies this if \
        # this is a network(multiplayer) game.
    def RegisterKeyPress(self, key, function):
        """Register a function callback for the given keyboard key."""
        self.key_pressed_dict[key] = function
    def RegisterKeyHeld(self, key, function):
        """Register a function callback for the given keyboard key (when held down)."""
        self.key_held_dict[key] = function
    def RegisterMousePress(self, button, function):
        """Register a function callback for the given mouse button when pressed."""
        self.mouse_dict[button] = function
    def SetSprite(self, sprite_instance):
        """Set the Players PyDark Sprite instance."""
        self.sprite = sprite_instance
    def SetControl(self, boolean):
        """
        Let's PyDark know if this Player can be controlled by the client.
        If this is a multiplayer game, the server also verifies that the client can move that player.
        """
        self.controllable = boolean
    def SetSurface(self, surface):
        """Set's the players sprite parent surface. Defines where the player sprite should be drawn onto."""
        self.sprite.surface = surface
    def SetPosition(self, position):
        """Set's the players sprite position."""
        return self.sprite.SetPosition(position)
    def GetSprite(self):
        """Returns a handle to the DarkSprite instance."""
        return self.sprite
    def GetCurrentImage(self):
        """Returns the current image that is being displayed for the player sprite."""
        return self.sprite.current_image
    def GetPosition(self):
        """Returns the players sprite position(x, y) coordinate as a Vector2d instance."""
        return vector2d.Vec2d(self.sprite.rect.topleft)
    def Collision(self, other=None):
        """Checks if the player object collides with another object."""
        pass
    def Update(self, clickEvent=None, hoverEvent=None, keyEvent=None, keyHeldEvent=None,
               keyChar=None, pos=None):
        """Player movement, actions, connection-state, etc are handled here."""
        if self.sprite is not None:
            if clickEvent:
                pass
            if hoverEvent:
                pass
            if keyEvent:
                keyChar = pygame.key.name(keyChar)
                key_handle = self.key_pressed_dict.get(keyChar)
                if key_handle is not None:
                    key_handle(keyChar)
            if keyHeldEvent:
                keyChar = pygame.key.name(keyChar)
                key_handle = self.key_held_dict.get(keyChar)
                if key_handle is not None:
                    key_handle(keyChar)                
            self.sprite.Update()
    def __repr__(self):
        if self.net is not None:
            return "Player: <%s>" %self.net.transport.getPeer()
        else:
            return "Player: <%s>" %self.name


class Block(object):
    """Terrain object that can optionally be created, moved, or destroyed."""
    def __init__(self, name, sprite):
        self.name = name
        self.sprite = sprite


class World(object):
    """World that holds all other objects. Size of world is determined /
       by size[0] * size[1] worth of Land() instances."""
    def __init__(self, name="World 1", size=(30, 30)):
        self.name = name
        self.width = size[0]
        self.height = size[1]


class Camera(object):
    """Object that controlls which part of the map to render /
       along with all other objects, including Player() instances."""
    def __init__(self, x, y, width=800, height=600):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    def Render(self, surface):
        """Renders the currently viewable portion of our surface(background)."""
        pass
    def Update(self):
        """In charge of scrolling and panning functionality for our camera instance."""
        pass


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
    return True


def read_hdd(fileName):
    f = file(fileName, "r")
    d = base64.b64decode(f.read())
    f.close()
    return d


def get_image_file(img):
    return pygame.image.load(img).convert_alpha()


def seticon(iconname):
    pygame.display.set_icon(pygame.image.load(iconname))


def preload(file_list, alpha=True):
    """Preload a list of files into memory. This function returns a list of pygame objects."""
    payload = []
    for entry in file_list:
        # Load images into memory.
        if entry.endswith(".png") or entry.endswith(".jpg") or entry.endswith(".gif"):
            if alpha:
                payload.append(pygame.image.load(entry).convert_alpha())
            else:
                payload.append(pygame.image.load(entry))
    return payload


class DarkSprite(pygame.sprite.Sprite):
    def __init__(self, name, starting_position=None, sprite_list=None,
                 sprite_sheet=None, depth=1):
        """Base PyDark 2D sprite. Takes 3 arguments: (name, starting_position, sprite_list)"""
        pygame.sprite.Sprite.__init__(self)
        self.focused = False # Allows us to test if the ChatBox has been focused(clicked on).
        self.name = name # name of our sprite (for reference)
        self.depth = depth
        self.index = 0 # Contains the index or counter to our current subsprite image.
        self.subsprites = [] # Subsprites for this DarkSprite instance.
        self.parent_sprite = None # Parent DarkSprite of this DarkSprite (if any)
        self.sprite_list = None
        self.text_location = None # Defines where to draw inputed text(if any)
        if sprite_list:
            self.sprite_list = sprite_list
        elif sprite_sheet:
            self.sprite_list = sprite_sheet
        self.starting_position = starting_position # starting position for sprite on Scene
        self.surface = None # sprite is drawn onto this surface \
        self.image = None # a handle to the main image for the sprite.
        self.current_image = None # a handle to the current subimage for the sprite images.
        self.text_surfaces = {} # dictionary of text surfaces to be drawn ontop of our sprite.
        self.hide = False # determines if we should display(render/draw) this sprite.
        self.rect = None
        self.scene = None # Contains a handle to the DarkSprites Scene.
    @staticmethod
    def CombineRects(first, second):
        """Combine the X and Y coordinates of two pygame.Rects together. Takes 2 parameters: (first, second). Must be DarkSprite instances."""
        return pygame.Rect(first.rect.left + second.rect.left,
                           first.rect.top + second.rect.top,
                           first.rect.width,
                           first.rect.height)
    def Draw(self, surface=None):
        if surface:
            surface.blit(self.image, self.rect)
        else:
            self.surface.blit(self.image, self.rect)
    def RenderChildren(self):
        """Draw subsprites onto this sprite."""
        #for k in self.subsprites:
            #self.current_image.blit(k.current_image, k.rect.topleft)
        pass
    def AddChild(self, darkspriteinstance):
        """Add a subsprite to this sprite."""
        darkspriteinstance.parent_sprite = self
        self.subsprites.append(darkspriteinstance)
    def LoadContent(self, filename=None, alpha=True, preloaded_sprite_list=None):
        # if user supplied a list of subsprites for animation.
        if preloaded_sprite_list:
            self.sprite_list = preloaded_sprite_list    
            self.image = self.sprite_list[self.index]
        elif self.sprite_list:
            self.sprite_list = [pygame.image.load(item).convert_alpha() for item in self.sprite_list]
            self.image = self.sprite_list[self.index]
        # otherwise, check if filename was supplied. If so, load that file as an image.
        else:
            if filename:
                if alpha:
                    self.image = pygame.image.load(filename).convert_alpha()
                else:
                    self.image = pygame.image.load(filename).convert()
        self.current_image = self.image
        # Ensure that an image was loaded.
        if not self.current_image:
            raise ValueError, "You must supply an image!"
        self.surface = pygame.Surface(self.current_image.get_size(), pygame.SRCALPHA, 32)
        self.rect = self.current_image.get_rect()
        return True
    def GetSize(self):
        """Returns the DarkSprites current images size. (width, height)."""
        return self.current_image.get_size()
    def AddText(self, fontHandle, fontColor, position, text,
                name="text1", redraw=False, redraw_function=None):
        textSurface = fontHandle.render(text, True, fontColor)
        textSurface = (textSurface, position, redraw, redraw_function, fontHandle, fontColor, text)
        self.text_surfaces[name] = textSurface
    def CreateBlock(self, width, height, color=(255, 255, 255, 255),
                    invisible=False):
        """Create a pygame.Surface object. Creates a block image."""
        if not invisible:
            self.image = pygame.Surface([width, height])
            self.image.fill(color)
        else:
            self.image = pygame.Surface([width, height], pygame.SRCALPHA, 32)
            self.image = self.image.convert_alpha()
        self.current_image = self.image
        self.surface = pygame.Surface(self.current_image.get_size(), pygame.SRCALPHA, 32)
        self.rect = self.image.get_rect()
    def CreateHexagon(self, color=(255, 255, 255, 255), size=[52, 52],
                      radius=21, x=42, y=42, rotate=27, invisible=False):
        point_list = Hexagon(radius, x, y, 0)
        if not invisible:
            self.image = pygame.Surface(size, pygame.SRCALPHA, 32)
            pygame.draw.polygon(self.image, color, point_list)
            self.image = self.image.convert_alpha()
        else:
            self.image = pygame.Surface(size, pygame.SRCALPHA, 32)
            pygame.draw.polygon(self.image, pygame.SRCALPHA, point_list)
            self.image = self.image.convert_alpha()
        if rotate != 0:
            self.image = pygame.transform.rotate(self.image, rotate)
        self.current_image = self.image
        self.surface = pygame.Surface(self.current_image.get_size(), pygame.SRCALPHA, 32)
        self.rect = self.image.get_rect()
    def Update(self, keyEvent=False, keyHeldEvent=False, keyChar=None):
        if self.surface is not None:
            self.surface.fill(pygame.SRCALPHA) # refresh(clear) transparent surface of previous drawings(blits).
            self.surface.blit(self.current_image, (0, 0))
            #self.process_subsprites(keyEvent, keyHeldEvent, keyChar)
            # draw text onto sprite.
            for key, value in self.text_surfaces.iteritems():
                # unpack values from Tuple
                j, pos, redraw, redraw_function, font_handle, font_color, text = value 
                # if redraw flag is True, then re-render the font text using the redraw_function.
                if redraw:
                    # Call the redraw_function and store its return value as a string.
                    text = str(redraw_function())
                    # Call the AddText class-method again to re-render the font surface.
                    self.AddText(font_handle, font_color, pos, text, key, redraw, redraw_function)
                self.surface.blit(j, pos)
            #self.process_subsprites(keyEvent, keyHeldEvent, keyChar)
            self.Step(keyEvent, keyHeldEvent, keyChar)
    def clear(self, i=None):
        self.surface.fill(pygame.SRCALPHA)
        if self.scene:
            if i is None:
                self.scene.Draw(item=self)
            else:
                self.scene.Draw(item=i)
        else:
            global game_instance
            self.scene = game_instance.get_current_scene()
    def Step(self, keyEvent, keyHeldEvent, keyChar):
        pass
    def process_subsprites(self, keyEvent, keyHeldEvent, keyChar):
        new_depth = self.depth + 1
        for k in self.subsprites:
            k.Update(keyEvent, keyHeldEvent, keyChar)
            self.scene.Draw(item=k)
    def process_subsprites2(self, keyEvent, keyHeldEvent, keyChar):
        """Called by parent DarkSprite. Handles drawing subsprites and passing events to them."""
        for k in self.subsprites:
            # draw subsprites.
            self.surface.blit(k.current_image, k.rect.topleft)
            for key, value in k.text_surfaces.iteritems():
                # unpack values from Tuple
                j, pos, redraw, redraw_function, font_handle, font_color, text = value 
                # if redraw flag is True, then re-render the font text using the redraw_function.
                if redraw:
                    # Call the redraw_function and store its return value as a string.
                    text = str(redraw_function())
                    # Call the AddText class-method again to re-render the font surface.
                    k.AddText(font_handle, font_color, pos, text, key, redraw, redraw_function)
                # Calculate this subsprites position by combining its text position /
                # with the parent DarkSprites position.
                new_pos = (k.rect.topleft[0] + pos[0], k.rect.topleft[1] + pos[1])
                self.surface.blit(j, new_pos)
    def OnKey(self, event):
        """Called when game.receive_user_input() is binded to this DarkSprite. Handles keystroke input."""
        pass
    def Collision(self, other):
        pass
    def OnClick(self, pos):
        """Called when user clicks on sprite."""
        pass
    def OnHover(self, pos):
        """Called when user hovers over the sprite."""
        pass
    def GetPosition(self):
        """Returns the DarkSprites current drawn position as a Vector2D object."""
        return vector2d.Vec2d(self.rect.topleft)
    def SetPosition(self, position=None):
        """Sets the sprites position(if passed), otherwise, it sets the sprite to the aforementioned starting position."""
        if self.rect:
            if position:
                self.rect.topleft = position
            else:
                self.rect.topleft = self.starting_position
            return True
        return False
    def ChangeImage(self, index):
        """Change the DarkSprites currently displayed image using an index."""
        self.index = index
        self.current_image = self.sprite_list[self.index]


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
            if isinstance(self.runafter, bool):
                print "waiting"
            else:
                time.sleep(self.runafter)
        self.func(self.params)
    

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
    def lookup_object(self, obj):
        """Attempts to find the object(obj) within' our self.objects list. Returns the index if found or None."""
        for item in self.objects:
            if item.name == obj.name:
                return self.objects.index(item)
        return None
    def add_object(self, obj):
        """Adds a object to our scene. If an object with the same name exists, it overwrites the old one."""
        found = self.lookup_object(obj)
        obj.scene = self
        if found:
            self.objects[found] = obj
        else:
            self.objects.append(obj)
    def add_player(self, player_instance):
        player_instance.SetSurface(self.surface)
        self.players.append(player_instance)
    def remove_object(self, obj):
        self.objects.remove(obj)
    def Draw(self, item=None):
        """Draw all self.objects onto our Scene() view."""
        if item is None:
            objects_sorted = sorted([j for j in self.objects], key=lambda s: s.depth, reverse=False)
            # draw our objects onto the Scene
            for item in objects_sorted:
                # Handle drawing our map
                if isinstance(item, Map):
                    pos = item.position
                    self.surface.screen.blit(item.tmxhandler.image, pos)
                # Handle drawing sprites
                elif isinstance(item, DarkSprite):
                    #self.surface.screen.blit(item.current_image, item.rect)
                    # if sprites self.hide attribute is False.
                    if not item.hide:
                        # Draw the DarkSprite surface.
                        if item.surface is not None:
                            self.surface.screen.blit(item.surface, item.rect)
                        # Draw the subsprites surfaces.
                        for k in item.subsprites:
                            if k.surface is not None:
                                k.Update(False, False, None)
                                self.surface.screen.blit(k.surface, k.rect)
                # Handle drawing UI overlay
                elif isinstance(item, ui.Overlay):
                    pos = item.position
                    item.Draw()
                    self.surface.screen.blit(item.surface, pos)
            # draw our players onto the Scene
            for PLAYER in self.players:
                if isinstance(PLAYER, Player):
                    self.surface.screen.blit(PLAYER.GetCurrentImage(), PLAYER.GetPosition())
        else:
            # Handle drawing our Map
            if isinstance(item, Map):
                pos = item.position
                self.surface.screen.blit(item.tmxhandler.image, pos)
            # Handle drawing players
            elif isinstance(item, Player):
                self.surface.screen.blit(item.GetCurrentImage(), item.GetPosition())
            # Handle drawing sprites
            elif isinstance(item, DarkSprite):
                if not item.hide:
                    if item.surface is not None:
                        self.surface.screen.blit(item.surface, item.rect)
                        # Draw the subsprites surfaces.
                for k in item.subsprites:
                    if k.surface is not None:
                        k.Update(False, False, None)
                        self.surface.screen.blit(k.surface, k.rect)
            # Handle drawing UI Overlay
            elif isinstance(item, ui.Overlay):
                item.Draw()
                pos = item.position
                self.surface.screen.blit(item.surface, pos)
    def Update(self, item=None):
        """Update all our self.objects on our Scene() view."""
        if item is None:
            for item in self.objects:
                item.Update()
            for player in self.players:
                player.Update()
        else:
            item.Update()
    def LoadMap(self, map_instance):
        self.map = map_instance
    def __repr__(self):
        return "<PyDark.engine.Scene: {0}>".format(self.name)
            

class Game(object):
    def __init__(self, title, window_size, icon=None,
                 center_window=True, FPS=30, online=False,
                 server_ip=None, server_port=None, protocol=None, log_or_not=False):
        """parameters: (title, window_size, icon, center_window, FPS, online, server_ip, server_port, protocol, log_or_not)"""
        self.debug = False
        self.clock = pygame.time.Clock()
        self.FPS = FPS
        self.elapsed = 0
        self.receive_input_for = None # defines which DarkSprite to receive input for.
        self.receive_input_for_keybind = None # defines which key stops(submits) receiving text input.
        self.receive_input_for_func = None # defines which function to call when the keybind above is pressed.
        # Dictionary containing keybinds and functions to invoke when pressed.
        self.key_pressed_binds = {}
        self.key_held_binds = {}
        # List of DarkSprites that we SHOULD ONLY catch evets for
        self.focused_sprites = []
        # List of UI elements that we SHOULD ONLY catch events for
        self.focus_on_ui = []
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
        self.CurrentScene = self.currentScene
        # default backgroundColor
        self.backgroundColor = (0, 0, 0)
        # wether or not we should center of our games window
        if center_window is True:
            ui.center_window()
        # let us know if we connected to the server properly(if applicable)
        self.connected = False
        # if game uses online features
        self.online = online
        self.server_ip = server_ip
        self.server_port = server_port
        self.protocol = protocol
        self.log_or_not = log_or_not
        self.connection = None
        self.network = None
        if online:
            if server_ip and server_port:
                self.create_online_connection()
            else:
                raise ValueError, "You must pass server_ip and server_port to your Game() instance"
            if not protocol:
                raise ValueError, "You must pass a PyDark.net.ClientProtocol!"
        # start pygame display
        self.initialize()
    def receive_user_input(self, darksprite, callback, keystroke="return"):
        """Instruct PyDark to transfer all keystrokes onto the target DarkSprites surface using the DarkSprites text_location."""
        if isinstance(darksprite, DarkSprite):
            if darksprite.text_location is not None:
                self.receive_input_for = darksprite
                self.receive_input_for_keybind = keystroke
                self.receive_input_for_func = callback
            else:
                raise ValueError, "You must set the DarkSprites text_location attribute!"
        else:
            raise ValueError, "You must specify a DarkSprite instance!"
    def stop_user_input(self):
        """Stop receiving user input from all DarkSprites."""
        self.receive_input_for = None
        self.receive_input_for_keybind = None
        self.receive_input_for_func = None
    def delete_object(self, instance):
        # removes an object completely from the game.
        found = False
        if isinstance(instance, ui.BaseSprite):
            if not found:
                for item in self.get_current_scene().objects:
                    if item.name == instance.name:
                        self.get_current_scene().remove_object(item)
                        found = True
                        break
                    if isinstance(item, ui.Overlay):
                        for entry in item.drawables.values():
                            if entry.name == instance.name:
                                item.remove_object(entry)
                                found = True
                                break
                
        elif isinstance(instance, DarkSprite):
            print "DarkSprite:", instance
    def register_key_pressed(self, keycode, function):
        """Register a function handle when the specified key is pressed."""
        self.key_pressed_binds[keycode] = function
    def register_key_held(self, keycode, function):
        """Register a function handle when the specified key is held."""
        self.key_held_binds[keycode] = function
    def remove_all_key_binds(self):
        """Remove all register key pressed and key held bindings."""
        self.key_pressed_binds = {}
        self.key_held_binds = {}
    def remove_key_bind(self, keycode):
        """Remove a function handle for the specified keybind."""
        try:
            self.key_pressed_binds.pop(keycode)
        except:
            pass

        try:
            self.key_held_binds.pop(keycode)
        except:
            pass
    def add_ui_focus_element(self, element):
        """Tell PyGame to only handle events for this UI element."""
        self.remove_focused_ui_element(element)
        self.focus_on_ui.append(element)
    def remove_focused_ui_element(self, element):
        """Remove this focused UI element."""
        if self.focus_on_ui.__contains__(element):
            self.focus_on_ui.remove(element)
    def focus_on_sprite(self, element):
        """Tell PyGame to only handle events for this DarkSprite."""
        self.remove_focused_sprite(element)
        self.focused_sprites.append(element)
    def remove_focused_sprite(self, element):
        """Remove focus from this DarkSprite."""
        if self.focused_sprites.__contains__(element):
            self.focused_sprites.remove(element)
    def clear_focused_ui_elements(self):
        """Clear all focused UI elements."""
        self.focus_on_ui = []
    def clear_focused_sprites(self):
        """Clear all focused DarkSprites."""
        self.focus_on_sprite = []
    def disable_debugging(self):
        self.debug = False
    def enable_debugging(self):
        self.debug = True
    def create_online_connection(self):
        try:
            self.connection = net.TCP_Client(parent=self, ip=self.server_ip, port=self.server_port,
                                             protocol=self.protocol, log_or_not=self.log_or_not,
                                             tick_function=self.tick, FPS=self.FPS)
            self.network = self.connection.factory
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
        global screen_hwnd, game_instance
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE)
        screen_hwnd = self.screen
        game_instance = self
        #write_hdd("icon.txt", convert_image_to_string(get_image_file("PyDark/preferences_desktop_gaming.png")) )
    def add_scene(self, _scene):
        self.scenes[_scene.name] = _scene
    def start(self):
        if len(list(self.scenes)) > 0:
            if not self.online:
                self.mainloop()
            else:
                # attempt to establish a connection to the games server.
                if self.connection:
                    self.connection.connect()

                # if we can't connect to the server, start the mainloop anyways.
                if not self.connection.factory.handle:
                    self.mainloop()
        else:
            raise ValueError, "You must supply at least one-scene."
    def OnClose(self):
        """Called when the game is closed."""
        pass
    def processEvent(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            if self.connection:
                self.connection.handle.disconnect()
            self.OnClose()
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.update_scene_objects(clickEvent=True)
            self.update_scene_players(clickEvent=True)
        elif event.type == pygame.MOUSEMOTION:
            if self.debug:
                print "Coordinate:", pygame.mouse.get_pos()
            self.update_scene_objects(hoverEvent=True)
            self.update_scene_players(hoverEvent=True)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.constants.K_BACKSPACE:
                char = pygame.constants.K_BACKSPACE
            else:
                char = event.unicode

            # If there's a DarkSprite that we are receiving text input for:
            if self.receive_input_for is not None:
                # If the key to stop receiving user input has been pressed.
                if pygame.key.name(event.key) == self.receive_input_for_keybind:
                  # Execute the binded function.
                    if self.receive_input_for_func is not None:
                        self.receive_input_for_func()
                    # Stop receiving user input.
                    self.stop_user_input()
                # Otherwise 
                else:
                    # Process events only for this DarkSprite.
                    self.receive_input_for.OnKey(event)
            else:
                # Otherwise, process events for everything.
                self.update_scene_objects(keyEvent=True, keyChar=char)
                self.update_scene_players(keyEvent=True, keyChar=event.key)
                self.handle_key_pressed_binds(keyEvent=True, keyChar=event.key)

    def handle_key_pressed_binds(self, keyEvent=False, keyChar=None):
        """Handles global key pressed(bind) events."""
        keyChar = pygame.key.name(keyChar)
        lookup = self.key_pressed_binds.get(keyChar)
        if lookup:
            lookup(keyChar)

    def update_scene_players(self, clickEvent=False, hoverEvent=False, keyEvent=False,
                             keyChar=None):
        """Handles user events for the client and commits updates on controllable Player() instances."""
        pos = pygame.mouse.get_pos()
        this_scene = self.get_current_scene()
        for person in this_scene.players:
            if person.controllable:
                if clickEvent:
                    person.Update(clickEvent=True, pos=pos)
                if hoverEvent:
                    person.Update(hoverEvent=True, pos=pos)
                if keyEvent:
                    person.Update(keyEvent=True, keyChar=keyChar)
    def update_scene_objects(self, clickEvent=False, hoverEvent=False, keyEvent=False,
                             keyChar=None):
        pos = pygame.mouse.get_pos()
        this_scene = self.get_current_scene()
        for item in this_scene.objects:
            if not item.hide:
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
                if isinstance(item, DarkSprite):
                    # This item is a DarkSprite.
                    self.handle_scene_objects(
                        pos,
                        item,
                        clickEvent,
                        hoverEvent,
                        keyEvent,
                        keyChar
                    )
    def handle_scene_objects(self, pos, item, clickEvent, hoverEvent, keyEvent,
                             keyChar):
        if len(self.focused_sprites) > 0:
            for e in self.focused_sprites:
                if clickEvent:
                    if e.rect.collidepoint(pos):
                        # fire the sprites OnClick() class-method.
                        e.OnClick(pos)
                        
                if hoverEvent:
                    if e.rect.collidepoint(pos):
                        # fire the sprites OnHover() class-method.
                        e.OnHover(pos)
        else:
            if clickEvent:
                if item.rect.collidepoint(pos):
                    # fire the sprites OnClick() class-method.
                    item.OnClick(pos)
                    
            if hoverEvent:
                if item.rect.collidepoint(pos):
                    # fire the sprites OnHover() class-method.
                    item.OnHover(pos)
    def handle_overlay_objects(self, pos, item, clickEvent, hoverEvent, keyEvent,
                               keyChar):

        # patch added on 1/8/2015.
        # Added list self.focus_on_ui which allows us to only catch events for specific UI elements.

        if len(self.focus_on_ui) > 0:
            for e in self.focus_on_ui:
                
                obj = item.drawables.get(e.name)

                if obj:
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
                    
        else:
            for e in item.drawables.keys():
                
                obj = item.drawables.get(e)

                if obj:
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
    def tick(self):
        for event in pygame.event.get():
            self.processEvent(event)

        self.Update()
        self.Draw()
        self.elapsed = self.clock.tick(self.FPS)
    def mainloop(self):
        while self.running:
            self.tick()
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


    

