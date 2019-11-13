import os
import socket
import sys

from constants import BUFFER_SIZE
from status_codes import CODE_WRITE_FILE, CODE_READ_FILE, CODE_OK
from web_format_converter import int32_to_web, int64_to_web, web_to_int
from status_codes import *
from receiver import receive_str, receive_file
from sender import send_file, send_str

def open_directory(sock, directory_name):
    sock.send(int32_to_web(CMD_OPEN_DIR))
    send_str(sock, directory_name)
    ret = receive_str(sock)
    print('cd response: ' + ret)

def read_directory(sock):
    sock.send(int32_to_web(CMD_READ_DIR))
    dir = receive_str(sock)
    print('ls response: ' + dir )

def make_directory(sock, directory_name):
    sock.send(int32_to_web(CMD_MAKE_DIR))
    send_str(sock, directory_name)
    ret = receive_str(sock)
    print('mkdir response: ' + ret)

def delete_directory(sock, directory_name):
    sock.send(int32_to_web(CMD_DELETE_DIR))
    send_str(sock, directory_name)
    ret = receive_str(sock)
    print('rmdir response: ' + ret)

def init_server(sock):
    sock.send(int32_to_web(CMD_INIT))
    ret = receive_str(sock)
    print('init response: ' + ret)

def main():
    #host = sys.argv[len(sys.argv) - 2]
    #port = int(sys.argv[len(sys.argv) - 1])
    host = 'localhost'
    port = 8800

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, port))

    # read_directory(sock)
    # make_directory(sock, 'hello')
    # read_directory(sock)
    # make_directory(sock, 'hi')
    # read_directory(sock)

    cmd = ''
    while True:
        inp = input('Enter command: ')
        cmd = inp.split(' ')[0]
        args = inp.split(' ')[1:]

        if cmd == 'cd' and len(args) == 1:
            open_directory(sock, args[0])
        elif cmd == 'ls' and len(args) == 0:
            read_directory(sock)
        elif cmd == 'mkdir' and len(args) == 1:
            make_directory(sock, args[0])
        elif cmd == 'rmdir' and len(args) == 1:
            delete_directory(sock, args[0])

        elif cmd == 'init' and len(args) == 0:
            init_server(sock)
        
        elif cmd == 'exit':
            print('Exiting')
            break
        else:
            print('Command-arguments combination unrecognized')

    sock.send(int32_to_web(CMD_CLOSE_SOCK))
    sock.close()

if __name__ == "__main__":
    main()
