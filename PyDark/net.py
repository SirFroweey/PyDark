import pygnetic
import logging
import socket

# change as necessary for changelog
__version__ = 1


class BaseServerProtocol(pygnetic.Handler):
    def __init__(self, message, **kwargs):
        logging.info("Received message: %s", message)
        print message
        

class Server(object):
    def __init__(self, name, port):
        pygnetic.init()
        self.server = pygnetic.Server(port=port, con_limit = 1000)
        self.name = name
        self.port = port
        self.ip = socket.gethostbyname(socket.gethostname())
    def build_protocol(self, handler):
        self.server.handler = handler
    def start(self):
        try:
            while True:
                self.server.update(1000)
        except KeyboardInterrupt:
            pass


class BaseClientProtocol(pygnetic.Handler):
    def __init__(self, message, **kwargs):
        print message


#if __name__ == "__main__":
#    s = Server(name="West Coast #1", ip="localhost", port=8000)
#    s.build_protocol(BaseServerProtocol)
#    s.start()
    



