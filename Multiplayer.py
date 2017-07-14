import socketserver
import socket

HOST, PORT = 'localhost', 8000
DATA_QUEUE = []

#################################
# If you are the request sender #
#################################

class requestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Get information
        data = self.request[0]
        socket = self.request[1]
        DATA_QUEUE.append(data)


DATA_QUEUE = []
SERVER = socketserver.UDPServer((HOST, PORT), requestHandler)
SERVER.serve_forever()


class requestSender():
    ''' Connect to the client and confirm seed '''
    def __init__():
        # TODO
        # Find and Connect to the server/client
        # Send a randomized seed
        # Wait for seed confirmation
        # Confirmed seed
        # Start game

    ''' Send data to the client '''
    def send_data(data):
        # TODO
        # data format: {'object': <object_type>, 'extra_data': <extra data associated with it>}

###################################
# If you are the request receiver #
###################################
