PyDark
======

PyDark is a 2D and Online Multiplayer video game framework written on-top of Python and PyGame. 

Our goal with PyDark was to make it easy to learn and integrate into existing pygame applications. PyDark is designed to be fully customizable and scalable, allowing developers to inherit base classes and make new sub-classes.

**Prerequisites:** Python 2.7.x, PyGame, Twisted


Overview
========
PyDark runs on top of PyDark.engine.Scene objects. A scene is a collection of objects that are displayed within' the scene. Think of it like a movie scene, where a series of scenes define a movie.

In a nutshell, you have a collection of modules avaialble to you, them being:
1. PyDark.engine (core functionality, i.e.: Scenes, Sprites, etc).
2. PyDark.ui (base UI elements for your game, integrate them into your games or build entirely new UI elements).
3. PyDark.net (twisted networking TCP and UDP client/server networking classes)
4. PyDark.io (series of functions and classes for file-access, SpriteSheet loading, encryption, map generation and much more)
5. PyDark.constants (classes that define PyDark event types)
6. PyDark.icon (static module containing base64 encoded string of base window icon)
7. PyDark.vector2d (contains base vector2d class for 2D vector math functionality) 

Examples
========
**Main menu**
> A simple example showcasing PyDarks UI module that displays a main menu scene. Keep in mind you'll be needing to manually provide the following files: (login_overlay_bg.jpg, input.png, input_selected.png, click.wav, button.png, button_hover.png).
```
import PyDark.engine
import PyDark.ui
import PyDark.vector2d


def login_button_pressed(event, game_instance):
    game_instance.currentScene = "game_scene"
    print event, event.fired_by
    print username.text
    print password.text


game = PyDark.engine.Game(
    title="FrowCraft",
    window_size=(800, 650),
    center_window=True,
    FPS=30,
    online=True,
    server_ip="localhost",
    server_port=8000
)

login_scene = PyDark.engine.Scene(surface=game, name="login_scene")
game_scene = PyDark.engine.Scene(surface=game, name="game_scene")

login_overlay = PyDark.ui.Overlay(
    parent=login_scene,
    size=(login_scene.window_size()[0], 330),
    image="login_overlay_bg.jpg",
    position=(0,0),
)


login_header = PyDark.ui.Label(
    name="login_header",
    text="FrowCraft",
    size=30,
    font="Arial",
    color=PyDark.engine.Color(255, 255, 255, 1),
    position=(100, 10),
    aa=True,
    center=True
)

username_label = PyDark.ui.Label(
    name="username_label",
    text="Username:",
    size=14,
    font="Arial",
    color=PyDark.engine.Color(0, 0, 0, 1),
    position=(0, 60),
    center=True
)

username = PyDark.ui.TextBox(
    name="username",
    position=(100, 80),
    center=True,
    default_image="input.png",
    image_selected="input_selected.png"
)

password_label = PyDark.ui.Label(
    name="password_label",
    text="Password:",
    size=14,
    font="Arial",
    color=PyDark.engine.Color(0, 0, 0, 1),
    position=(0, 150),
    center=True
)

password = PyDark.ui.TextBox(
    name="password",
    position=(0, 170),
    center=True,
    default_image="input.png",
    image_selected="input_selected.png"
)

login_button = PyDark.ui.Button(
    name="login_button",
    position=(100, 260),
    on_press=lambda e, game=game:login_button_pressed(e, game),
    center=True,
    sound="click.wav",
    default_image="button.png",
    image_hover="button_hover.png",
    image_selected="button_hover.png"
)

login_overlay.add_object(login_header)
login_overlay.add_object(username_label)
login_overlay.add_object(username)
login_overlay.add_object(password_label)
login_overlay.add_object(password)
login_overlay.add_object(login_button)

login_scene.add_object(login_overlay)

game.add_scene(login_scene)
game.add_scene(game_scene)

game.currentScene = "login_scene"
game.start()
```

`login_overlay.add_object(OBJECT)`
> Adds an object to our PyDark.ui.Overlay object. This will draw OBJECT on-top of the overlay object. An overlay defines a section of the screen to draw UI elements on).

`login_scene.add_object(OBJECT)`
> Adds an object to a scene, the scene being the login_scene. Needed to display an object during a scene. Only required to do so once.

`game.add_scene(SCENE)`
> Adds a scene to our game instance. Needed to specify which scenes we are going to make available for our game.

`game.currentScene = "login_scene"`
> Defines the current scene to display on our game.

`game.start()`
> Start main game loop.

Networking
==========
Networking in PyDark is event-based and is built to keep things simple for client/server communication. One way PyDark acheives this is by supplying functions to modify python dictionaries that contain the make-up of your networking logic.

An example of this is via PyDark.net.ServerProtocol.headers and PyDark.net.ClientProtocol.headers. These instance variables are python dictionaries that will contain (key, value) pairs consisting of (header, callback).

**header**
> unique (string) that defines this networking packet (data) type. An example is 'msg' and 'login'. These of course are arbitrary, you can name your headers whatever you want. 

**callback**
> class-method (function) callback to trigger when we receive a packet with this header.

In PyDark we call these things handles. So to register a new handle in your protocol, do something like:

```
import PyDark.net

class MyProtocol(PyDark.net.ClientProtocol):
    def __init__(self, factory, log):
        PyDark.net.ClientProtocol.__init__(self, factory, log)
        self.register_handle("msg", self.chat_message)
    def chat_message(self, payload):
        print "Payload:", payload
        self.message("msg:Thanks for the welcome message!")

```
*(Client protocol example)*

Notice the line: `self.register_handle("msg", self.chat_message)`.
This line tells PyDark.net that we want to call the chat_message class-method after receiving a 'msg' packet from the server.
In the back-end PyDark.net processes all communication between the server and client by calling packet.split(":"). 
This will split the packet with two values (header, data). Thus your packets should be in the format of "header:data".
You can send this packet via your ClientProtocol or ServerProtocol by calling `self.message("msg:your message here")`. 
**Note:** Ensure colons(:) are filtered out to prevent the PyDark.net code from generating an IndexError.


```
import PyDark.net

class OurProtocol(PyDark.net.ServerProtocol):
    def __init__(self, factory):
        PyDark.net.ServerProtocol.__init__(self, factory)
        self.register_handle("msg", self.chat_message)
        
    def chat_message(self, payload):
        print "Payload:", payload
        
    def clientConnected(self, player_or_peer):
		print "{player_or_peer} has connected!".format(player_or_peer=player_or_peer)
		self.message("msg:hello, world!")
```
*(Server protocol example)*

**Note:** it is possible to use PyDark.net networking code outside an PyDark.engine.Game() instance. Take a look at the client.py and server.py examples on how to acheive that.

**Real PyDark implementation**
> The best and easiest way to create a networked game in PyDark is to create two (or more) files named client.py and server.py. Your client code should store your PyDark game and client networking logic (PyDark.net.ClientProtocol sub-class, Sprites, Tilsheets, Scenes, Mainloop, etc). While the server.py file should only store PyDark.net server networking logic.

With this in mind, the way you specify your game is an online game is via the following example:

```
game = PyDark.engine.Game(
    title="FrowCraft",
    window_size=(800, 650),
    center_window=True,
    FPS=30,
    online=True,
    server_ip="localhost",
    server_port=8000,
    protocol=OurProtocol
)
```
Pay close attention to the `online=True`, `server_ip="localhost"`, `server_port=8000`, and `protocol=MyProtocol` keyword arguments.
These inform PyDark that our game instance is an online game instance and we specify which IP and PORT to connect to. Finally,
we specify our PyDark.net.ClientProtocol instance as the games networking protocol.

In the back-end, PyDark will attempt to connect to the server. If a connection is successful, the instance variable `game.connection` will return a PyDark.net.TCP_Client instance and the instance variable `game.network` will return a PyDark.net.*Factory instance. Otherwise, both varaibles will be None.





