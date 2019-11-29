import shutil
import socket
from threading import Thread
import time

from constants_and_codes import *
from helpers import *

import random

def ping_naming_server():
    print('Attempting to contact naming server.')
    naming_server_sock = open_socket(NAMING_SERVER_IP, int(NAMING_SERVER_PORT))
    while not naming_server_sock:
        print('Could not connect to naming server. Pining again after 20 seconds.')
        time.sleep(20)
        naming_server_sock = open_socket(NAMING_SERVER_IP, int(NAMING_SERVER_PORT))
    print('Connected to naming server!')
    send_code(naming_server_sock, CMD_PING_FROM_STORAGE)
    ret = receive_code(naming_server_sock)
    if ret != CODE_OK:
        return False
    return True

def ping_from_naming(sock):
    send_code(sock, CODE_OK)

def initialize():

    try:  # Delete storage files directory and all its content
        shutil.rmtree(STORAGE_SERVER_ROOT_PATH)
    except OSError as e:
        print("Error deleting storage directory: %s - %s." % (e.filename, e.strerror))

    try:  # Recreate the storage files directory
        os.mkdir(STORAGE_SERVER_ROOT_PATH)
    except OSError as e:
        print("Error creating storage files directory: %s - %s." % (e.filename, e.strerror))

    print('Storage server initalization complete.')

def create_file(sock):
    # TO-DO
    return

def read_file(sock):
    file_name = receive_str(sock)
    file_path = STORAGE_SERVER_ROOT_PATH + '/' + file_name
    if not os.path.isfile(file_path):
        print('Client trying to read a file that does not exist on the server.')
        send_code(sock, FILE_NOT_EXIST_ON_STORAGE_SERVER)
        sock.close()
        return
    send_code(sock, CODE_OK)
    send_file(sock, file_path)

def write_file(sock):
    # Get file name (id) and receive it
    file_name = receive_str(sock)
    receive_file(sock, STORAGE_SERVER_ROOT_PATH + '/' + file_name)
    send_code(sock, CODE_OK)

    # Send receive confirmation to naming server
    naming_server_sock = open_socket(NAMING_SERVER_IP, NAMING_SERVER_PORT)
    send_code(naming_server_sock, CMD_CONFIRM_FILE_UPLOAD)
    send_str(naming_server_sock, file_name)

def delete_file(sock):
    file_name = receive_str(sock)
    file_path = STORAGE_SERVER_ROOT_PATH + '/' + file_name
    if os.path.exists(file_path):
        os.remove(file_path)
        send_code(sock, CODE_OK)
        print("File " + file_name + " deleted.")
    else:
        send_code(sock, FILE_NOT_EXIST_ON_STORAGE_SERVER)
        print('File to delete does not exist on server.')

def copy_file(sock):
    # names are ids in this case
    old_file_name = receive_str(sock)
    old_file_path = STORAGE_SERVER_ROOT_PATH + '/' + old_file_name
    new_file_name = receive_str(sock)
    new_file_path = STORAGE_SERVER_ROOT_PATH + '/' + new_file_name
    
    if os.path.exists(old_file_path):
        shutil.copyfile(old_file_path, new_file_path)
        send_code(sock, CODE_OK)
    else:
        send_code(sock, FILE_NOT_EXIST_ON_STORAGE_SERVER)
        print('File to copy does not exist on storage server.')

def replicate_file(sock):
    source_address = receive_str(sock)
    file_name = receive_str(sock)

    file_path = STORAGE_SERVER_ROOT_PATH + '/' + file_name

    source_storage_sock = open_socket(source_address, STORAGE_SERVER_PORT)
    send_code(source_storage_sock, CMD_READ_FILE)
    send_str(source_storage_sock, file_name)
    ret = receive_code(source_storage_sock)
    if ret != CODE_OK:
        print("File to replicate does not exist on source storage server.")
        return
    receive_file(source_storage_sock, file_path)
    print("File " + file_name + " replicated.")
    send_code(sock, CODE_OK)

class ClientListener(Thread):
    def __init__(self, name: str, sock: socket.socket):
        super().__init__(daemon=True)
        self.sock = sock
        self.name = name

    def _close(self):
        self.sock.close()
        #print(self.name + ' disconnected')

    def run(self):
        #print('Waiting for command from ' + self.name)
        cmd = receive_code(self.sock)
        print('Received ' + str(cmd) + ' from ' + self.name)

        if cmd == CMD_INIT: initialize()
        elif cmd == CMD_FILE_CREATE: create_file(self.sock)
        elif cmd == CMD_READ_FILE: read_file(self.sock)
        elif cmd == CMD_WRITE_FILE: write_file(self.sock)
        elif cmd == CMD_DELETE_FILE: delete_file(self.sock)
        elif cmd == CMD_COPY_FILE: copy_file(self.sock)
        elif cmd == CMD_REPLICATE_FILE: replicate_file(self.sock)
        elif cmd == CMD_PING_FROM_NAMING: ping_from_naming(self.sock)
        else: print('Unknown command from ' + self.name)

        self.sock.close()

if __name__ == "__main__":

    initialize()

    # Create directory to receive files
    if not os.path.isdir(STORAGE_SERVER_ROOT_PATH):
        os.mkdir(STORAGE_SERVER_ROOT_PATH)

    if ping_naming_server():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', STORAGE_SERVER_PORT))
        sock.listen()

        #sock.settimeout(10)  # for testing

        while True:
            connection, address = sock.accept()
            ClientListener(str(address[0]), connection).start()
    else:
        print('Could not ping naming server. Exiting!')
