from itertools import chain
import datetime
import constants
import pygame
import string
import time
import os


def connection_status(screen, position, status=None):
    if status is None:
            color = 0xff0000
    elif status:
        color = 0x00ff00
    else:
        color = 0xffff00
    screen.fill(color, (5 + position[0], position[1], 15, 15))


def Color(r, g, b, a):
    return pygame.Color(r, g, b, a)


class Event(object):
    """
    An Event() is triggered(created) when a UI action is performed, such as:
    - a mouse click
    - a key is pressed
    - a key is released
    - mouse hovers over a UI element
    - etc
    """
    def __init__(self, _type, fired_by, **kwargs):
        self.type = _type
        self.fired_by = fired_by
        self.kwargs = kwargs
    def __repr__(self):
        return "<PyDark.ui.Event: {0}>".format(self.type)
    

class BaseSprite(pygame.sprite.Sprite):
    def __init__(self, position, depth=1, hide=False, parent=None):
        pygame.sprite.Sprite.__init__(self)
        self.hide = False # determine if this should be drawn
        self.parent = parent # sprite parent (if any), used for precise collision checking.
        self.depth = depth # sprite depth(z-index)
        self.surface = None
        self.center = False
        self.focus = False # patch on 1/8/2015. Allows us to only handle events for this sprite and nothing else.
        self.focused = False
        self.in_hover = False
        self.adjusted = False
        self.psurface = False
        self.position = position
        self.x, self.y = self.position
        self.last_image_change_timestamp = datetime.datetime.now()

    def Draw(self, surface):
        if self.center:
            if not self.adjusted:
                x = (surface.get_size()[0]/2) - (self.size[0]/2)
                y = self.position[1]
                self.set_xy(x, y)
                self.rect.topleft = self.position
                self.adjusted = True
        surface.blit(self.surface, self.rect)

    def set_wh(self, w, h):
        self.w = w
        self.h = h

    def set_xy(self, x, y):
        self.position = (x, y)
        self.x = y
        self.y = y

    def collides(self, surface):
        return self.y < surface.top + surface.height and self.y + self.h > surface.top and self.x < surface.left + surface.width and self.x + self.w > surface.left

    def getCoords(self):
        return self.position


class TextBox(BaseSprite):
    def __init__(self, name, position, fontName="Tahoma",
                 fontSize=14, fontColor=(255, 255, 255, 0), default_image=None,
                 image_hover=None, image_selected=None,
                 offset=(15, 28), center=False, max_length=20):
       # Call the parent class (Sprite) constructor
       BaseSprite.__init__(self, position)
       self.name = name
       self.text = ""
       self.allowed_keys = string.letters[:52] + string.digits + string.punctuation + " "
       self.center = center
       self.font = pygame.font.SysFont(fontName, fontSize)
       self.fontColor = fontColor
       # offset defines where the text should be rendered within' our image.
       self.offset = offset

       # default values
       self.default_image = None
       self.image_hover = None
       self.image_selected = None

       # set default global variable values
       if default_image:
           self.default_image = pygame.image.load(default_image).convert_alpha()
       if image_hover:
           self.image_hover = pygame.image.load(image_hover).convert_alpha()
       if image_selected:
           self.image_selected = pygame.image.load(image_selected).convert_alpha()

       self.image = self.default_image
       self.size = self.default_image.get_size()
       # create an invisible pygame.Surface
       self.surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA, 32)

       # Fetch the rectangle object that has the dimensions of the image
       # Update the position of this object by setting the values of rect.x and rect.y
       self.rect = self.image.get_rect()
       # Set position of our sprite
       self.rect.topleft = position
       # Store position in global variable
       self.position = position
       self.max_length = max_length

    def change_image(self, image):
        # Every half-a-second w check to see the state of the image.
        # Wether its focused, being hovered by the mouse, etc.
        if image:
            comparison = self.last_image_change_timestamp  - datetime.datetime.now()
            if abs(comparison.total_seconds()) > 0.5:
                self.image = image
                self.last_image_change_timestamp  = datetime.datetime.now()

    def set_text(self):
        self.Update(None, None, None)

    def Update(self, mouseCoords=None, clickEvent=False, hoverEvent=False):
        fontSurface = self.font.render(self.text, True, self.fontColor)
        centered_x = (self.image.get_width() - fontSurface.get_width())/2
        self.surface.blit(self.image, (0, 0))
        self.surface.blit(fontSurface, self.offset)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position

        if mouseCoords:
            mouse_position = pygame.mouse.get_pos()

            # If sprite has a parent.
            # Create a new pygame.Rect() object and combine the parents coordinates with /
            # this sprites coordinates for precise collision checking.
            if self.parent:
                top = self.rect.top + self.parent.rect.top
                left = self.rect.left + self.parent.rect.left
                self.test_rect = pygame.Rect(left, top,
                                             self.rect.width, self.rect.height)
            else:
                self.test_rect = self.rect

            # check for mouse input
            if pygame.mouse.get_pressed() == (1, 0, 0):
                if self.test_rect.collidepoint(mouse_position):
                    self.focused = True
                    self.change_image(image=self.image_selected)
                else:
                    self.focused = False
                    self.change_image(image=self.default_image)
            # check for mouse hover
            else:
                if self.image_hover:
                    if self.test_rect.collidepoint(mouse_position):
                        self.in_hover = True
                        self.change_image(image=self.image_hover)
                    else:
                        self.in_hover = False
                        self.change_image(image=self.default_image)
    def __call__(self):
        return self._textbox
    def __repr__(self):
        return "<PyDark.ui.TextBox: {0}>".format(self.name)
    

class Button(BaseSprite):
    """
    A button is a UI element that handles mouse click events.
    Example:
    def hello_world(event):
        print event
    my_button = Button(name="button1", text="Hello, World", position=(0,0), on_press=self.hello_world)
    """
    def __init__(self, name, text=None, textcolor=(255, 255, 255, 1), default_image=None,
                 image_selected=None, image_hover=None,
                 font="Arial", fontsize=12, position=(0,0), on_press=None,
                 offset=None, center=False, sound=None):
        BaseSprite.__init__(self, position)
        self.name = name
        self.text = text
        
        # default values
        self.default_image = None
        self.image_hover = None
        self.image_selected = None

        # last time the button was clicked
        self.last_click = datetime.datetime.now()

        # set default global variable values
        if default_image:
            self.default_image = pygame.image.load(default_image).convert_alpha()
                
        if image_hover:
            self.image_hover = pygame.image.load(image_hover).convert_alpha()
        if image_selected:
            self.image_selected = pygame.image.load(image_selected).convert_alpha()

        self.surface = pygame.Surface(self.default_image.get_size(), pygame.SRCALPHA, 32)
            
        self.textcolor = textcolor
        self.font = font
        self.fontsize = fontsize
        self.position = position
        self.on_press = on_press
        self.offset = offset
        self.center = center
        if sound:
            sound = pygame.mixer.Sound(sound)
        self.image = default_image
        self.sound = sound
        self.build()
    def build(self):
        if self.default_image:
            self._button = self.default_image
            self.rect = self._button.get_rect()
        self.size = self._button.get_size()
        self.set_wh(self._button.get_size()[0], self._button.get_size()[1])
        self.rect.topleft = self.position
        self.set_text()
    def change_image(self, image):
        # Check to see the state of the image.
        # Wether its focused, being hovered by the mouse, etc.
        if image:
            comparison = self.last_image_change_timestamp  - datetime.datetime.now()
            if abs(comparison.total_seconds()) > 0.01:
                self._button = image
                self.last_image_change_timestamp  = datetime.datetime.now()
    def set_text(self, new_text=None):
        if new_text:
            self.text = new_text
            self.build()

        if self.text:
            f = pygame.font.SysFont(self.font, self.fontsize)
            text = f.render(self.text, False, self.textcolor)
            if self.offset:
                self._button.blit(text, self.offset)
            else:
                x = (self.size[0] - text.get_size()[0]) / 2
                y = (self.size[1] - text.get_size()[1]) / 2
                self._button.blit(text, (x, y))
    def Update(self, mouseCoords=None, clickEvent=False, hoverEvent=False):
        self.surface.blit(self._button, (0, 0))
        self.rect = self._button.get_rect()
        self.rect.topleft = self.position

        if mouseCoords:
            mouse_position = pygame.mouse.get_pos()

            # If sprite has a parent.
            # Create a new pygame.Rect() object and combine the parents coordinates with /
            # this sprites coordinates for precise collision checking.
            if self.parent:
                top = self.rect.top + self.parent.rect.top
                left = self.rect.left + self.parent.rect.left
                self.test_rect = pygame.Rect(left, top,
                                             self.rect.width, self.rect.height)
            else:
                self.test_rect = self.rect

            # Check for mouse input
            if pygame.mouse.get_pressed() == (1, 0, 0):
                if self.test_rect.collidepoint(mouse_position):
                    comparison = self.last_click  - datetime.datetime.now()
                    if abs(comparison.total_seconds()) > 0.2:
                        self.focused = True
                        self.change_image(image=self.image_selected)
                        if self.sound: self.sound.play()
                        time.sleep(0.3)
                        self.on_press(Event(constants.CLICK_EVENT, self))
                        self.last_click = datetime.datetime.now()
                else:
                    self.focused = False
                    self.change_image(image=self.default_image)
            # Check for mouse hover
            if hoverEvent:
                if self.image_hover:
                    if self.test_rect.collidepoint(mouse_position):
                        self.in_hover = True
                        self.change_image(image=self.image_hover)
                    else:
                        self.in_hover = False
                        self.change_image(image=self.default_image)               
    #def Draw(self, surface):
    #    if self.center:
    #        if not self.adjusted:
    #            x = (surface.get_size()[0]/2) - (self.size[0]/2)
    #            y = self.position[1]
    #            self.position = (x, y)
    #            self.set_xy(x, y)
    #            self.rect.topleft = self.position
    #            self.adjusted = True
    #    surface.blit(self._button, self.position)
    def __call__(self):
        return self._button
    def __repr__(self):
        return "<PyDark.ui.Button: {0}>".format(self.name)
        

class Label(BaseSprite):
    """
    A label is a UI element that displays text.
    Example:
    hello = Label(name="label1", text="Hello, World")
    """
    def __init__(self, name, text, size=14, font="Arial",
                 color=Color(0,0,0,0), aa=False, position=(0,0),
                 center=False):
        BaseSprite.__init__(self, position)
        self.name = name
        self.text = text
        self.position = position
        self.color = color
        self.f = pygame.font.SysFont(font, size)
        self._label = self.f.render(text, aa, color)
        self.surface = pygame.Surface(self._label.get_size(), pygame.SRCALPHA, 32)
        self.center = center
        self.set_wh(self._label.get_size()[0], self._label.get_size()[1])
        self.size = self._label.get_size()
    #def size(self):
    #    return self._label.get_size()
    def set_text(self, text):
        self.text = text
        self._label = self.f.render(self.text, True, self.color)
    def Update(self, mouseCoords=None, clickEvent=False, hoverEvent=False):
        self.surface.blit(self._label, (0, 0))
        self.rect = self._label.get_rect()
        self.rect.topleft = self.position
    #def Draw(self, surface):
    #    if self.center:
    #        if not self.adjusted:
    #            x = (surface.get_size()[0]/2) - (self.size()[0]/2)
    #            y = self.position[1]
    #            self.position = (x, y)
    #            #print self.name, x, y
    #            super(Label, self).set_xy(x, y)
    #            self.adjusted = True
    #    surface.blit(self._label, self.position)
    def __call__(self):
        return self._label
    def __repr__(self):
        return "<PyDark.ui.Label: {0}>".format(self.name)


class Dialog(BaseSprite):
    def __init__(self, name, position, image, icon, icon_position,
                 title, message, message_color, message_size, message_position,
                 title_position, title_color, font, title_size,
                 button_instance, customFont=False,
                 offset=(20, 20), center=False):
        BaseSprite.__init__(self, position)
        self.position = position
        self.center = center
        self.title = title
        self.name = name
        self.icon = pygame.image.load(icon).convert_alpha()
        self.image = pygame.image.load(image).convert_alpha()
        self.rect = self.image.get_rect()
        self.size = self.image.get_size()
        self.surface = pygame.Surface(self.size, pygame.SRCALPHA, 32)
        self.icon_position = icon_position
        self.title_position = title_position
        self.title_color = title_color
        self.font = font
        self.title_size = title_size
        self.customFont = customFont
        self.message = message
        self.message_color = message_color
        self.message_size = message_size
        self.message_position = message_position
        self.button_instance = button_instance
    def Update(self, mouseCoords=None, clickEvent=False, hoverEvent=False):
        self.rect.topleft = self.position
        self.surface.blit(self.image, (0, 0))
        self.surface.blit(self.icon, self.icon_position)
        # display title
        display_text(
            surface=self.surface,
            text=self.title,
            font=self.font,
            fontColor=self.title_color,
            fontSize=self.title_size,
            customFont=self.customFont,
            pos=self.title_position,
        )
        # display message(body)
        display_text(
            surface=self.surface,
            text=self.message,
            font=self.font,
            fontColor=self.message_color,
            fontSize=self.message_size,
            customFont=self.customFont,
            pos=self.message_position,
        )
        # call buttons Update class-method to pass event-handling.
        self.button_instance.Update(mouseCoords, clickEvent, hoverEvent)
        # display button
        self.surface.blit(self.button_instance._button, self.button_instance.rect.topleft)


class Tabbed_Window(BaseSprite):
    def __init__(self, name, position, image, icon, icon_position,
                 title, message, message_color, message_size, message_position,
                 title_position, title_color, font, title_size, customFont=False,
                 offset=(20, 20), center=False):
        BaseSprite.__init__(self, position)
        self.position = position
        self.center = center
        self.title = title
        self.name = name
        if icon:
            self.icon = pygame.image.load(icon).convert_alpha()
        else:
            self.icon = None
        self.image = pygame.image.load(image).convert_alpha()
        self.rect = self.image.get_rect()
        self.size = self.image.get_size()
        self.surface = pygame.Surface(self.size, pygame.SRCALPHA, 32)
        if icon_position:
            self.icon_position = icon_position
        else:
            self.icon_position = None
        self.title_position = title_position
        self.title_color = title_color
        self.font = font
        self.title_size = title_size
        self.customFont = customFont
        self.message = message
        self.message_color = message_color
        self.message_size = message_size
        self.message_position = message_position
    def Update(self, mouseCoords=None, clickEvent=False, hoverEvent=False):
        self.rect.topleft = self.position
        self.surface.blit(self.image, (0, 0))
        if self.icon:
            self.surface.blit(self.icon, self.icon_position)
        # display title
        display_text(
            surface=self.surface,
            text=self.title,
            font=self.font,
            fontColor=self.title_color,
            fontSize=self.title_size,
            customFont=self.customFont,
            pos=self.title_position,
        )
        # display caption
        display_text(
            surface=self.surface,
            text=self.message,
            font=self.font,
            fontColor=self.message_color,
            fontSize=self.message_size,
            customFont=self.customFont,
            pos=self.message_position,
        )        
    

class Overlay(object):
    """
    An overlay whose purpose is to draw UI elements in-top of it. A UI frame.
    Parameters: (parent, size)
    Example:
    frame = Overlay(parent=self, size=(300, 250))
    frame.Load(Button(name="button1", text="Submit", position=(0,0), on_press=self.on_press))
    """
    def __init__(self, name, parent, size, color=None, endcolor=None, image=None,
                 invisible=False, position=(0,0), depth=1, hide=False):
        self.depth = depth
        self.hide = hide
        self.position = position
        self.drawables = dict()
        self.parent = parent
        self.image = image
        self.name = name
        if image:
            self.panel = pygame.image.load(image).convert_alpha()
        else:
            if not invisible:
                self.panel = pygame.Surface(size).convert()
                self.panel.fill(color)
                if color and endcolor:
                    fill_gradient(self.panel, color, endcolor)
                self.invisible = False
            else:
                self.panel = pygame.Surface(size, pygame.SRCALPHA, 32)
                self.invisible = True
        # added 1/8/2015 as a patch to "refresh" the panel surface.
        self.surface = pygame.Surface(size, pygame.SRCALPHA, 32)
        self.size = size
        self.color = color
        self.endcolor = endcolor
    def redraw_surface(self):
        if not self.image:
            self.panel.fill(self.color)
            if self.color and self.endcolor:
                fill_gradient(self.panel, self.color, self.endcolor)        
    def add_object(self, element):
        self.drawables[element.name] = element
    def remove_object(self, element):
        try:
            self.drawables.pop(element.name)
        except KeyError:
            pass
    def Center(self, element):
        if element.center:
            if not element.adjusted:
                x = (self.surface.get_size()[0]/2) - (element.size[0]/2)
                y = element.position[1]
                element.set_xy(x, y)
                element.rect.topleft = self.position
                element.adjusted = True        
    def Draw(self, element=None):
        self.surface.blit(self.panel, (0, 0))
        if element is None:
            drawables_sorted = sorted([j[1] for j in self.drawables.items()], key=lambda s: s.depth, reverse=False)
            for element in drawables_sorted:
                if element.center:
                    self.Center(element)
                self.surface.blit(element.surface, element.rect)
                #element.Draw(self.panel)
        else:
            #element.Draw(self.panel)
            if element.center:
                self.Center(element)
            self.surface.blit(element.surface, element.rect)
    def Update(self, element=None):
        if element is None:
            for name, element in self.drawables.iteritems():
                element.Update()
        else:
            element.Update()
    def __repr__(self):
        return "<PyDark.ui.Overlay({0}, {1}) at ({2}, {3})>".format(
            self.size[0], self.size[1], self.position[0], self.position[1])
            
    

def set_window_position(x, y):
    """Set the window's position on the monitor. example: set_window_position(100, 100)"""
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)


def center_window():
    """Set's the window's position to the center of the monitor."""
    os.environ['SDL_VIDEO_CENTERED'] = '1'


def fill_gradient(surface, color, gradient, rect=None, vertical=True, forward=True):
    """fill a surface with a gradient pattern
    Parameters:
    color -> starting color
    gradient -> final color
    rect -> area to fill; default is surface's rect
    vertical -> True=vertical; False=horizontal
    forward -> True=forward; False=reverse
    
    Pygame recipe: http://www.pygame.org/wiki/GradientCode
    """
    if rect is None: rect = surface.get_rect()
    x1,x2 = rect.left, rect.right
    y1,y2 = rect.top, rect.bottom
    if vertical: h = y2-y1
    else:        h = x2-x1
    if forward: a, b = color, gradient
    else:       b, a = color, gradient
    rate = (
        float(b[0]-a[0])/h,
        float(b[1]-a[1])/h,
        float(b[2]-a[2])/h
    )
    fn_line = pygame.draw.line
    if vertical:
        for line in range(y1,y2):
            color = (
                min(max(a[0]+(rate[0]*(line-y1)),0),255),
                min(max(a[1]+(rate[1]*(line-y1)),0),255),
                min(max(a[2]+(rate[2]*(line-y1)),0),255)
            )
            fn_line(surface, color, (x1,line), (x2,line))
    else:
        for col in range(x1,x2):
            color = (
                min(max(a[0]+(rate[0]*(col-x1)),0),255),
                min(max(a[1]+(rate[1]*(col-x1)),0),255),
                min(max(a[2]+(rate[2]*(col-x1)),0),255)
            )
            fn_line(surface, color, (col,y1), (col,y2))

    
def truncline(text, font, maxwidth):
        real=len(text)       
        stext=text           
        l=font.size(text)[0]
        cut=0
        a=0                  
        done=1
        old = None
        while l > maxwidth:
            a=a+1
            n=text.rsplit(None, a)[0]
            if stext == n:
                cut += 1
                stext= n[:-cut]
            else:
                stext = n
            l=font.size(stext)[0]
            real=len(stext)               
            done=0                        
        return real, done, stext             

        
def wrapline(text, font, maxwidth):
    """
    Wraps text into a single-line pretty format for UI purposes. Returns a list.
    Parameters: (text, font, maxwidth)
    """
    done=0                      
    wrapped=[]                  
                               
    while not done:             
        nl, done, stext=truncline(text, font, maxwidth) 
        wrapped.append(stext.strip())                  
        text=text[nl:]                                 
    return wrapped
 
 
def wrap_multi_line(text, font, maxwidth):
    """
    Wraps text into a multi-line pretty format for UI purposes. Returns a list.
    Parameters: (text, font, maxwidth)
    """
    lines = chain(*(wrapline(line, font, maxwidth) for line in text.splitlines()))
    return list(lines)


def display_text(surface, text, font="Arial", fontColor=(0,0,0), fontSize=14, customFont=False, pos=(0,0)):
    """Display text on a surface. Parameters: (surface, fontname, fontsize, position)"""
    if not customFont:
        f = pygame.font.SysFont(font, fontSize)
    else:
        f = pygame.font.Font(font, fontSize)
    s = f.render(text, 1, fontColor)
    surface.blit(s, pos)

