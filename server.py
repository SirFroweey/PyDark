import PyDark.net


# FrowCraft server instance.

SERVER_PORT = 8000
SERVER_NAME = "FrowServer West #1"


class FrowProtocol(PyDark.net.BaseServerProtocol):
    def __init__(self):
        PyDark.net.BaseServerProtocol.__init__(self)
        

class FrowServer(PyDark.net.Server):
    def __init__(self):
        PyDark.net.Server.__init__(self, SERVER_NAME, SERVER_PORT)


if __name__ == "__main__":
    server = FrowServer()
    server.build_protocol(FrowProtocol)
    print "\nServer started on {0}:{1}\n".format(server.ip, server.port)
    server.start()


