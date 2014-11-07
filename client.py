import PyDark.net


SERVER_PORT = 8000
SERVER_IP = "localhost"


class MyProtocol(PyDark.net.ClientProtocol):
    def __init__(self, factory):
        PyDark.net.ClientProtocol.__init__(self, factory)
        self.register_handle("msg", "self.chat_message(payload)")
    def chat_message(self, payload):
        print "Payload:", payload


Client = PyDark.net.TCP_Client(
    ip=SERVER_IP,
    port=SERVER_PORT,
    protocol=MyProtocol
)


Client.connect()
