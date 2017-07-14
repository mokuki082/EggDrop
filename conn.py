import sys, time
import socketserver, socket
import threading
import pygame
from sprites import *

'''
Communication Guide (C means confirmation required):
C   To connect to a chicken:
        "hi:<initial_seed>"

C   To re-position a chicken:
        "ch:<x_position>"

    To tick (request increment seed):
        "ti:<x_position>:<y_velocity>"

    To tock (confirm increment seed):
        "to:<x_position>:<y_velocity>"

    To delete an object:
        "de:<obj_id>"

    To update opponent on self hp:
        "hp:<value>"
'''
########################
### Global Variables ###
########################
THIS_HOST, THIS_PORT = None, None # Customized
THEIR_HOST, THEIR_PORT = None, None # Customized
UDP_CLIENT = None # Fixed through out a game

'''
Allows Communication to another player
    *_addr is a tuple: (<host_address>, <port>)
'''
class ChickenConn():
    class UDPHandler(socketserver.BaseRequestHandler):
        def handle(self): # Got some data from the opponent
            # Data format: obj_type:obj_info
            global UDP_CLIENT
            global OPPONENT_COOR
            data = self.request[0].decode('utf-8').split(':')
            if not UDP_CLIENT:
                if data[0] == 'hi':
                    UDP_CLIENT = self.client_address # Only take requests from this client
                    # Send back Hi
                    self.request[1].sendto(bytes('hi','utf-8'), self.client_address)
            elif UDP_CLIENT == self.client_address:
                if data[0] == 'ch':
                    OPPONENT_COOR = (float(data[1]), float(data[2]))
                    self.request[1].sendto(b'', self.client_address)
    # END OF CLASS "UDPHandler"

    def __init__(self, this_addr, their_addr, screen):
        # Set global variables
        global THIS_HOST, THIS_PORT, THEIR_HOST, THEIR_PORT
        THIS_HOST, THIS_PORT = this_addr
        THEIR_HOST, THEIR_PORT = their_addr
        # Set sprites/objects
        self.waitscreen = ConnectionWaitScreen()
        # Start a UDP Server
        self.server = socketserver.UDPServer((THIS_HOST, THIS_PORT), UDPHandler)
        self.handler_thread = threading.Thread(target=self.handler_thread_init)
        self.handler_thread.start()
        self.opponent_socket = None
        max_time = 60 # If no server can be reached after max_time, raise timeout exception
        while max_time: # Keep sending 'hi' requests to see if the other server is alive
            print("Finding opponent")
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(bytes('hi','utf-8'), (THEIR_HOST, THEIR_PORT))
            try:
                sock.settimeout(0.5)
                recv = sock.recv(16)
                if recv.decode('utf-8') == 'hi':
                    print('Server reached!')
                    self.opponent_socket = sock
                    self.opponent_socket.settimeout(0.05)
                    return
            except socket.timeout:
                pass
            time.sleep(0.2)
            max_time -=1
            self.waitscreen.render(screen)
            pygame.display.update()
        # An error occurred
        print("An error occurred during connection.")
        self.server.shutdown()
        self.handler_thread.join()

    def handler_thread_init(self):
        self.server.serve_forever()

    def talk(self,data):
        self.opponent_socket.sendto(bytes('box:' + data, 'utf-8'), (THEIR_HOST, THEIR_PORT))
        time.sleep(0.02)

    def listen(self):
        return self.opponent_socket.recv(16)

# END OF CLASS "ChickenConn"
