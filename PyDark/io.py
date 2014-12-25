# PyDark modules
import engine
# Python standard library
from xml.dom.minidom import parseString
from xml.dom.minidom import Node
import itertools
import struct
import os


def GetFolder(name):
    """Returns absolute location on DISK DRIVE, if the specified folder exists."""
    current_dir = os.getcwd()
    if os.path.exists(os.path.join(current_dir, name)):
        return os.path.join(current_dir, name)
    raise IOError, "Could not find folder: {0}".format(os.path.join(current_dir, name))


def GetFile(path, name):
    """Returns absolute location on DISK DRIVE, if the specified file exists."""
    if os.path.exists(os.path.join(path, name)):
        return os.path.join(path, name)
    raise IOError, "Could not load: {0}".format(os.path.join(path, name))


def xor_encrypt(string, key):
    """Encrypt a string using XOR encryption. Takes two parameters: (string, key(integer))"""
    chars = []
    for char in string:
        char = ord(char) ^ key
        char = struct.pack('B', char)
        chars.append(char)
    chars = "".join(chars)
    return chars


def xor_decrypt(string, key):
    """Decrypt a string using XOR decryption. Takes two parameters: (string, key(integer))"""
    chars = []
    for char in string:
        char = struct.unpack('B', char)[0]
        char = char ^ key
        char = chr(char)
        chars.append(char)
    chars = "".join(chars)
    return chars


class CustomFile(object):
    def __init__(self, name):
        """Create and build a custom file. I.E.: CustomFile(fileName).build()"""
        self.name = name
        self.buffer = ""
    def populate(self, data):
        self.buffer += str(data)
    def clean(self):
        self.buffer = self.buffer.replace("(", "[")
        self.buffer = self.buffer.replace(")", "]")
        self.buffer = self.buffer.replace("'", "")
        self.buffer = self.buffer.replace("u", "")
    def build(self):
        f_obj = open(self.name, "w")
        f_obj.write(self.buffer)
        f_obj.close()


class TileSet(object):
    def __init__(self, element):
        self.images = {}
        self.firstgid = int(element.attributes['firstgid'].value)
        self.name = element.attributes['name'].value
        self.tilewidth = int(element.attributes['tilewidth'].value)
        self.tileheight = int(element.attributes['tileheight'].value)
        self.iterate_through_images(element)
    def iterate_through_images(self, element):
        for image in element.childNodes:
            if image.nodeType == Node.ELEMENT_NODE:
                source = image.attributes['source'].value
                #height = image.attributes['height'].value
                #width = image.attributes['width'].value
                self.images[os.path.basename(source)] = engine.SpriteSheet(source)
    def __repr__(self):
        return "<PyDark.engine.TileSet: {0}>".format(self.name)


class MapCompiler:
    """Map loader. Required .tmx extension"""
    def __init__(self, fileName):
        """Map(fileName). You need to call .load() on your Map instance."""
        self.layout = None
        self.tilesets = {}
        self.headers = {}
        self.map = None
        self.array = []
        #
        if fileName[-4:] != ".tmx":
            fileName = fileName + ".tmx"
        #
        self.fileName = fileName
        self.file = file(fileName, "r")
        self.xml = self.file.read()
        self.file.close()
    def build(self):
        """Load the .tmx map into memory."""
        self.map = parseString(self.xml)
        self.iterate_through_headers()
        self.iterate_through_tilesets()
        self.iterate_through_map()
        self.parse_tilesets()
        self.build_pydarkmap_file()
    def generate_gid_array(self, name, tileset):
        images = tileset.images
        tile_width = tileset.tilewidth
        tile_height = tileset.tileheight
        for k in images.keys():
            k = images.get(k)
            x_values = [x for x in range(tile_width, k.width+tile_width, tile_width)]
            y_values = [q for q in range(tile_height, k.height+tile_height, tile_height)]
            almost = [(k.filename, i[0], i[1]) for i in zip(x_values, y_values)]
            self.array += almost
    def parse_tilesets(self):
        for name, tileset in self.tilesets.iteritems():
            self.generate_gid_array(name, tileset)
    def build_pydarkmap_file(self):
        """Builds a PyDark MAP file."""
        counter = 1
        changed_name = self.fileName.replace(".tmx", ".txt")
        f = CustomFile(changed_name)
        for key, value in self.headers.iteritems():
            data = "{0}={1}\n".format(key, value)
            f.populate(data)
        for o in self.array:
            o = "{0}={1}\n".format(counter, o)
            f.populate(o)
            counter += 1
        f.populate("world=")
        f.populate(self.layout)
        f.clean()
        f.build()        
    def iterate_through_headers(self):
        """Extract the attributes from the <map> XML tag. Orientation, width, etc."""
        root_element = self.map.getElementsByTagName('map')[0]
        for k in root_element.attributes.keys():
            v = root_element.attributes[k].value
            self.headers[k] = v
    def iterate_through_tilesets(self):
        for entry in self.map.getElementsByTagName('tileset'):
            self.tilesets[entry.attributes['name'].value] = TileSet(entry)
    def iterate_through_map(self):
        row = []
        for t in self.map.getElementsByTagName('tile'):
            t = t.attributes['gid'].value
            row.append(t)
        self.layout = list(itertools.izip_longest(*[iter(row)]*int(self.headers.get('width'))))
        # The following code makes the world lists pretty.
        self.layout = "".join(["\n\t" + str(j) for j in self.layout])
        self.layout = "[" + self.layout + "\n]"



        
