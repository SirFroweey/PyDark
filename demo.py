from pygame.locals import *
import datetime
import pygame


__author__ = "David Almendarez"
__website__ = "www.findadownload.net"


#######################################################
# NOTE: This is not a part of PyDark.
# This file simply teaches you how to create UI elements outside of PyDark /
# in native PyGame.
#######################################################


#############################
# TextInput Sprite example. #
#############################
# This file teaches you how to create User-Interface objects, like TextInputs.
# Our TextInput is a subclass of a pygame.sprite.Sprite object.
# The way it works is simple, first we load the images supplied by the TextInput instance.
# Then we create an invisible pygame.Surface() called self.surface.
# Then we render our textinput image on-top of the invisible pygame.Surface().
# Then we render our text(fontSurface) on-top of the textinput image.
# Then we blit or draw the self.surface(pygame.Surface) object on our screen buffer(screen).
#####
# Resources: http://www.moosader.com/create/
#####


class BaseSprite(pygame.sprite.Sprite):
    def __init__(self, position):
        pygame.sprite.Sprite.__init__(self)
        self.active = False
        self.in_hover = False
        self.position = position
        self.last_image_change_timestamp = datetime.datetime.now()

    def draw(self):
        s = pygame.display.get_surface()
        s.blit(self.surface, self.rect)


class TextInput(BaseSprite):
    def __init__(self, position, fontName="Tahoma",
                 fontSize=14, fontColor=(255, 255, 255, 0), default_image=None,
                 image_hover=None, image_selected=None,
                 offset=(15, 28)):
       # Call the parent class (Sprite) constructor
       BaseSprite.__init__(self, position)
       self.font = pygame.font.SysFont(fontName, fontSize)
       self.text = ""
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
       # create an invisible pygame.Surface
       self.surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA, 32)

       # Fetch the rectangle object that has the dimensions of the image
       # Update the position of this object by setting the values of rect.x and rect.y
       self.rect = self.image.get_rect()
       # Set position of our sprite
       self.rect.topleft = position
       # Store position in global variable
       self.position = position

    def change_image(self, image):
        # Every half-a-second w check to see the state of the image.
        # Wether its focused, being hovered by the mouse, etc.
        if image:
            comparison = self.last_image_change_timestamp  - datetime.datetime.now()
            if abs(comparison.total_seconds()) > 0.5:
                self.image = image
                self.last_image_change_timestamp  = datetime.datetime.now()

    def update(self):
        fontSurface = self.font.render(self.text, True, self.fontColor)
        centered_x = (self.image.get_width() - fontSurface.get_width())/2
        self.surface.blit(self.image, (0, 0))
        self.surface.blit(fontSurface, self.offset)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position

        # check for mouse input
        if pygame.mouse.get_pressed() == (1, 0, 0):
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.active = True
                self.change_image(image=self.image_selected)
            else:
                self.active = False
                self.change_image(image=self.default_image)


FPS = 30
pygame.init()
run_game = True
screen = pygame.display.set_mode((640, 480))

username_input = TextInput(
    default_image="input.png",
    image_selected="input_selected.png",
    position=(100, 100),
)

clock = pygame.time.Clock()
while run_game:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run_game = False
        elif event.type == pygame.KEYDOWN:
            char, key = event.unicode, event.key
            if username_input.active:
                if key == K_BACKSPACE:
                    username_input.text = username_input.text[:-1]
                else:
                    username_input.text += char

                print "Entered:", username_input.text
                

    screen.fill((0, 255, 0, 1))
    username_input.update()
    username_input.draw()
    
    pygame.display.flip()

pygame.quit()
