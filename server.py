import PyDark.net


SERVER_PORT = 8000
SERVER_NAME = "FrowServer West #1"
MAX_CLIENTS = 1000


class OurProtocol(PyDark.net.ServerProtocol):
    def __init__(self, factory):
        PyDark.net.ServerProtocol.__init__(self, factory)
        self.register_handle("msg", "self.chat_message(payload)")
    def chat_message(self, payload):
        print "Payload:", payload

        
Server = PyDark.net.TCP_Server(
    name=SERVER_NAME,
    port=SERVER_PORT,
    log2file=False,
    max_clients=MAX_CLIENTS,
    protocol=OurProtocol
)


Server.start()
