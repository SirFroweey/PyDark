import PyDark.net


SERVER_PORT = 8500
SERVER_IP = "localhost"


class MyProtocol(PyDark.net.ClientProtocol):
    def __init__(self, factory, log):
        PyDark.net.ClientProtocol.__init__(self, factory, log)
        self.register_handle("msg", self.chat_message)
    def chat_message(self, payload):
        print "Payload:", payload
        self.message("msg:Thanks for the welcome message!")


Client = PyDark.net.TCP_Client(
    parent=None,
    log_or_not=True,
    ip=SERVER_IP,
    port=SERVER_PORT,
    protocol=MyProtocol
)


Client.connect()
