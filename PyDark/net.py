from twisted.internet.protocol import ClientFactory, DatagramProtocol
from twisted.internet import protocol, reactor, endpoints
#from twisted.application import service, internet
from twisted.protocols.basic import LineReceiver
from twisted.internet.task import LoopingCall
from twisted.internet import task
from twisted.python import log
import sys
#
import engine


__version__ = 2.0


def ord2base(number, base):
    """
    Gets a number and converts it to the specified numeric base value.

    Parameters:
    number = integer
    base = integer (numeric_base)
    """
    if number == 0: return ''
    number, remainder = divmod(number, base)
    return ord2base(number, base)+str(remainder)


def encode_packet(data, numeric_base=4, seperator="5", reverse=True):
    """
    Encode packet data.

    Parameters:
    data = string (payload)
    numeric_base = integer (numeric base to convert our character ordinal numbers)
    seperator = string (character or characters to split our encoded packet) [Ensure this character(s) is unique]
    reverse = boolean (wether we should reverse our encoded packet or not)
    """
    data = str(seperator).join([ord2base(ord(j), numeric_base) for j in data])
    if reverse:
        data = data[::-1]
    return data


def decode_packet(data, numeric_base=4, seperator="5", reverse=True):
    """
    Decode our encoded packet data.

    Parameters:
    data = string (payload)
    numeric_base = integer (numeric base to decode our character ordinal numbers)
    seperator = string (character or characters to split our encoded packet) [Ensure this character(s) is unique]
    reverse = boolean (wether we should reverse our packet data or not before decoding it)
    """
    if reverse:
        data = data[::-1]
    chars = [unichr(int(str(j), numeric_base)) for j in data.split(seperator)]
    return "".join(chars)


class ClientProtocol(LineReceiver):
    """
    Base Client protocol.
    Sub-class this to create your protocol.
    """
    
    def __init__(self, factory, log):
        self.factory = factory
        self.headers = {}
        self.iterables = []
        self.log = log
        self.connected = False
        self.debug_mode = False

    def get_hash(self):
        value = 0
        keys = [int("0x" + j.encode('hex'), 16) for j in self.headers.keys()]
        for j in keys:
            value += j
        return value

    def register_iterable(self, headerName):
        if self.headers.get(headerName):
            self.iterables.append(headerName)
        else:
            raise ValueError, "You must first register the handle {0} via register_handle(headerName), before registering it as an iterable.".format(headerName)

    def register_handle(self, headerName, func):
        """
        Register packet handle for our server.
        
        Parameters:
        headerName = string, i.e.: "MSG"
        func = function handle
        """
        self.headers[headerName] = func

    def connectionMade(self):
        self.connected = True

    def packetParser(self, line):
        """
        This function is in charge of 'splitting' the packet header from the packet payload.
        By default, it seperates the header from the payload by splitting the packet data from its colon(:).
        """
        header, payload = line.split(":")
        return header, payload

    def badPacket(self, line):
        """
        This function is called when an unrecognized packet is received from the server.
        """
        print "Received unrecognized packet from server:", line

    def lineReceived(self, line):
        try:
            # ensure we get a clean packet
            line = self.factory.decryption(line)
            header, payload = self.packetParser(line)
        except:
            # if we get a malformed packet, close the connection.
            self.badPacket(line)
            header = None
            self.transport.loseConnection()

        # ensure we have a handle to this header.
        if header is not None:
            header = header.lower()
            command = self.headers.get(header)
            if command is not None:
                try:
                    command(payload)
                except:
                    print "[Error on handle: {0}. Payload: {1}]".format(
                        header,
                        payload,
                    )
                    print str(sys.exc_info())

    def message(self, line):
        self.sendLine(self.factory.encryption(line))


class ServerProtocol(LineReceiver):
    """
    Base Server protocol.
    Sub-class this to create your protocol.
    """

    def __init__(self, factory):
        self.factory = factory
        # list of protocol handles. Expand as necessary. Always pass (payload) as parameter.
        self.headers = {}
        self.iterables = []
        self.debug_mode = False

    def get_hash(self):
        value = 0
        keys = [int("0x" + j.encode('hex'), 16) for j in self.headers.keys()]
        for j in keys:
            value += j
        return value

    def register_iterable(self, func):
        """
        Register a function(class-method) that will run indefinetly on the server.
        """
        self.iterables.append(func)

    def remove_iterable(self, func):
        """
        Remove a registered function(class-method) that is running indefinetly on the server.
        """
        try:
            self.iterables.remove(func)
        except ValueError:
            pass

    def remove_iterables(self):
        """
        Remove all registered functions(class-method) that are running indefinetly on the server.
        """
        self.iterables = []

    def register_handle(self, headerName, func):
        """
        Register packet handle for our server.
        
        Parameters:
        headerName = string, i.e.: "MSG"
        func = function handle
        """
        self.headers[headerName] = func

    def maxClients(self):
        """
        Called when the maximum amount of players QUOTA has been reached on the server.
        By default, this function sends a DISCONNECT packet to the client and calls transport.loseConnection() after.
        """
        self.message("DISCONNECT: Too many connections. Please try again later.", self.transport.getPeer())
        self.transport.loseConnection()        
    
    def connectionMade(self):
        client = engine.Player(network=self) # create a temporary Player() instance.
        #log.msg("Got client connection from %s" % client)
        if len(self.factory.clients) >= self.factory.max_clients:
            self.maxClients()
        else:
            self.factory.clients[client.net.transport] = client
            #log.msg("Updated client hash-table: %s" %self.factory.clients.keys())
            self.factory.activeConnections += 1

    def lookupPlayer(self, instance, key_supplied=False):
        """Looks for the Player() instance on our self.factory.clients list."""
        # if we did NOT pass the dictionary key as instance.
        if not key_supplied:
            # get the client via its key(transport)
            return self.factory.clients.get(instance.transport)
        # otherwise, get the client via its supplied key(transport)
        return self.factory.clients.get(instance)

    def connectionLost(self, reason):
        self.clientDisconnected()
        client = self.lookupPlayer(self)#self.transport.getPeer()
        if client is not None:
            # Lost connection due to internet problems, random disconnect, etc
            #log.msg("Lost connection from %s" %client)
            self.factory.clients.pop(client.net.transport)
        #log.msg("Disconnect Reason: %s" %reason)
        self.factory.activeConnections -= 1

    def clientDisconnected(self):
        """Called when a client loses connection to the server."""
        pass

    def broadcastMessage(self, line, client=None):
        """Broadcast line to all clients or to an individual client(if 'client' is passed as an argument)."""
        if not client:
            for c in list(self.factory.clients.keys()):
                _player = self.lookupPlayer(c, key_supplied=True)
                _player.net.message(line)
        else:
            client.net.message(line)

    def broadcast_message(self, line, client=None):
        """Broadcast line to all clients or to an individual client(if 'client' is passed as an argument)."""
        if not client:
            for c in list(self.factory.clients.keys()):
                _player = self.lookupPlayer(c, key_supplied=True)
                _player.net.message(line)
        else:
            client.net.message(line)

    def packetParser(self, line):
        """
        This function is in charge of 'splitting' the packet header from the packet payload.
        By default, it seperates the header from the payload by splitting the packet data from its colon(:).
        """
        header, payload = line.split(":")
        return header, payload

    def badPacket(self, line):
        """
        This function is called when an unrecognized packet is received from the server.
        """
        print "Received unrecognized packet from server:", line

    def closeConnection(self):
        """Kicks the current client off the server by closing its connection."""
        self.transport.loseConnection()
        
    def lineReceived(self, line):
        try:
            # ensure we get a clean packet
            line = self.factory.decryption(line)
            header, payload = self.packetParser(line)
        except:
            # if we get a malformed packet, close the connection.
            ####
            # We should also store the client ip and port and keep track of how many \
            # malformed packets we receive from them.
            ####
            # That way we can detect patterns and determine if the client is a hacker \
            # and is attempting to send edited packet data.
            self.badPacket(line)
            header = None
            self.transport.loseConnection()

        # ensure we have a handle to this header.
        if header is not None:
            header = header.lower()
            command = self.headers.get(header)
            if command is not None:
                try:
                    command(payload)
                except:
                    print "[Error on handle: {0}. Payload: {1}]".format(
                        header,
                        payload,
                    )
                    print str(sys.exc_info())

    def message(self, line):
        self.sendLine(self.factory.encryption(line))


class ServerUDPProtocol(DatagramProtocol):
    """Base UDP ServerProtocol class."""

    def __init__(self, factory):
        self.factory = factory
        # list of protocol handles. Expand as necessary. Always pass (payload) as parameter.
        self.headers = {}
        self.iterables = []
        self.debug_mode = False

    def get_hash(self):
        value = 0
        keys = [int("0x" + j.encode('hex'), 16) for j in self.headers.keys()]
        for j in keys:
            value += j
        return value

    def lookupPlayer(self, instance, key_supplied=False):
        """Looks for the Player() instance on our self.factory.clients list."""
        # if we did NOT pass the dictionary key as instance.
        if not key_supplied:
            # get the client via its key(transport)
            return self.factory.clients.get(instance.transport)
        # otherwise, get the client via its supplied key(transport)
        return self.factory.clients.get(instance)

    def register_iterable(self, func):
        """
        Register a function(class-method) that will run indefinetly on the server.
        """
        self.iterables.append(func)

    def remove_iterable(self, func):
        """
        Remove a registered function(class-method) that is running indefinetly on the server.
        """
        try:
            self.iterables.remove(func)
        except ValueError:
            pass

    def remove_iterables(self):
        """
        Remove all registered functions(class-method) that are running indefinetly on the server.
        """
        self.iterables = []

    def register_handle(self, headerName, func):
        """
        Register packet handle for our server.
        
        Parameters:
        headerName = string, i.e.: "MSG"
        func = function handle
        """
        self.headers[headerName] = func

    def broadcastMessage(self, line, client=None):
        """Broadcast line to all clients or to an individual client(if 'client' is passed as an argument)."""
        if not client:
            for c in list(self.factory.clients.keys()):
                _player = self.lookupPlayer(c, key_supplied=True)
                _player.net.message(line)
        else:
            client.net.message(line)

    def broadcast_message(self, line, client=None):
        """Broadcast line to all clients or to an individual client(if 'client' is passed as an argument)."""
        if not client:
            for c in list(self.factory.clients.keys()):
                _player = self.lookupPlayer(c, key_supplied=True)
                _player.net.message(line)
        else:
            client.net.message(line)
    
    def maxClients(self):
        """
        Called when the maximum amount of players QUOTA has been reached on the server.
        """
        self.transport.loseConnection()
        
    def packetParser(self, line):
        """
        This function is in charge of 'splitting' the packet header from the packet payload.
        By default, it seperates the header from the payload by splitting the packet data from its colon(:).
        """
        header, payload = line.split(":")
        return header, payload

    def badPacket(self, line):
        """
        This function is called when an unrecognized packet is received from the server.
        """
        print "Received unrecognized packet from server:", line

    def closeConnection(self):
        """Kicks the current client off the server by closing its connection."""
        self.transport.loseConnection()
        
    def datagramReceived(self, line, address):
        if len(self.factory.clients) >= self.factory.max_clients:
            self.maxClients()
        else:
            if not self.factory.clients.get(address):
                client = engine.Player(network=self)
                self.factory.clients[client.net.transport] = client
                self.factory.activeConnections += 1
        
        try:
            line = self.factory.decryption(line)
            header, payload = self.packetParser(line)
        except:
            # if we get a malformed packet, close the connection.
            self.badPacket(line)
            header = None
            self.transport.loseConnection()

        # ensure we have a handle to this header.
        if header is not None:
            header = header.lower()
            command = self.headers.get(header)
            if command is not None:
                try:
                    command(payload)
                except:
                    print "[Error on handle: {0}. Payload: {1}]".format(
                        header,
                        payload,
                    )
                    print str(sys.exc_info())
                    
    def message(self, line):
        self.transport.write(line)
        

class PyDarkFactory(protocol.Factory):
    # max_clients = maximum active connections
    def __init__(self, parent, name, max_clients, protocol, encryption,
                 decryption):
        self.name = name
        self.activeConnections = 0
        self.encryption = encryption
        self.decryption = decryption
        self.parent = parent
        self.max_clients = max_clients
        self.protocol = protocol
        self.clients = {} #hash table. quick look ups.
        #self.clients = {transport: Player() instance}
        
    def buildProtocol(self, addr):
        return self.protocol(self)


class PyDarkClientFactory(ClientFactory):

    def __init__(self, parent, protocol, log, encryption,
                 decryption):
        self.activeConnections = 0
        self.encryption = encryption
        self.decryption = decryption
        self.parent = parent
        self.protocol = protocol
        self.clients = {} # hash table. quick look ups.
        self.log = log
        self.handle = None

    def buildProtocol(self, addr):
        self.handle = self.protocol(self, self.log)
        return self.handle

    def clientConnectionFailed(self, connector, reason):
        log.msg('connection failed: ' + reason.getErrorMessage())
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        log.msg('connection lost: ' + reason.getErrorMessage())
        reactor.stop()


class UDP_Server(object):
    def __init__(self, name="", ip="127.0.0.1", port=9020, log2file=True, max_clients=100,
                 protocol=ServerProtocol, encryption=encode_packet,
                 decryption=decode_packet, FPS=30):
        self.FPS = FPS
        self.name = name
        self.port = port
        if log2file:
            log.startLogging(open('server_log.txt', 'w'))
        else:
            log.startLogging(sys.stdout)
        self.protocol = protocol
        self.handler = PyDarkFactory(self, name, max_clients, protocol,
                                     encryption, decryption)
        reactor.listenUDP(port, self.handler, interface=ip)
    def start(self):
        reactor.run()
    def __repr__(self):
        return "Server: {0} on port {1}".format(self.name, self.port)


class TCP_Server(object):
    def __init__(self, name="", ip="127.0.0.1", port=9020, log2file=True, max_clients=100,
                 protocol=ServerProtocol, encryption=encode_packet,
                 decryption=decode_packet, FPS=30):
        self.FPS = FPS
        self.name = name
        self.port = port
        if log2file:
            log.startLogging(open('server_log.txt', 'w'))
        else:
            log.startLogging(sys.stdout)
        self.protocol = protocol
        self.handler = PyDarkFactory(self, name, max_clients, protocol,
                                     encryption, decryption)
        #self.s = endpoints.serverFromString(reactor, "tcp:%s:interface=%s" %(str(port), str(ip))).listen(
        #    self.handler
        #)
        reactor.listenTCP(port, self.handler, interface=ip)
    def start(self):
        reactor.run()
    def __repr__(self):
        return "Server: {0} on port {1}".format(self.name, self.port)


class TCP_Client(object):
    def __init__(self, parent, ip, port, protocol=ClientProtocol,
                 log_or_not=False, tick_function=None, FPS=30,
                 encryption=encode_packet, decryption=decode_packet):
        if log_or_not:
            log.startLogging(sys.stdout)
        self.parent = parent
        self.protocol = protocol
        self.port = port
        self.ip = ip
        self.factory = PyDarkClientFactory(self, protocol, log_or_not,
                                           encryption, decryption)
        self.tick_function = tick_function
        self.handle = None # handle to our client reactor.
        self.FPS = FPS
    def connect(self):
        self.handle = reactor.connectTCP(self.ip, self.port, self.factory)
        tick = LoopingCall(self.tick_function)
        tick.start(1.0 / self.FPS)
        reactor.run()



        
