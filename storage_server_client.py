import os
import socket
import sys

from constants import STORAGE_SERVER_PORT, CLIENT_ROOT_PATH
from receiver import receive_file, receive_str
from sender import send_str, send_file
from status_codes import CMD_WRITE_FILE, CMD_READ_FILE, CODE_OK, CMD_CREATE_EMPTY_FILE, CMD_DELETE_FILE, \
    CMD_FILE_INFO, CMD_COPY_FILE
from web_format_converter import int32_to_web, web_to_int


def get_file_info(sock, file_name):
    send_str(sock, file_name)

    code = web_to_int(sock.recv(32))
    if code != CODE_OK:
        raise Exception('error with code %d' % code)

    file_info = receive_str(sock)
    print(file_info)


def create_empty_file(sock, file_name):
    send_str(sock, file_name)

    code = web_to_int(sock.recv(32))
    if code != CODE_OK:
        raise Exception('error with code %d' % code)
    else:
        print('file created')


def delete_file(sock, file_name):
    send_str(sock, file_name)

    code = web_to_int(sock.recv(32))
    if code != CODE_OK:
        raise Exception('error with code %d' % code)
    else:
        print('file removed')


def copy_file(sock, old_file_name, new_file_name):
    send_str(sock, old_file_name)
    send_str(sock, new_file_name)

    code = web_to_int(sock.recv(32))

    if code != CODE_OK:
        raise Exception('error with code %d' % code)
    else:
        print('file copied')


def read_file(sock, file_name):
    send_str(sock, file_name)

    code = web_to_int(sock.recv(32))

    if code != CODE_OK:
        raise Exception('error with code %d' % code)

    receive_file(sock, file_name, CLIENT_ROOT_PATH)


def write_file(sock, file_name):
    if not os.path.exists(CLIENT_ROOT_PATH + file_name):
        raise Exception('file does not exist')

    send_str(sock, file_name)
    send_file(sock, file_name, CLIENT_ROOT_PATH)


def send_command_to_storage_server(host, args):
    port = STORAGE_SERVER_PORT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, port))

    command = args[0]
    if command == 'w':
        sock.send(int32_to_web(CMD_WRITE_FILE))
        write_file(sock, args[1])
    elif command == 'r':
        sock.send(int32_to_web(CMD_READ_FILE))
        read_file(sock, args[1])
    elif command == 'c':
        sock.send(int32_to_web(CMD_COPY_FILE))
        copy_file(sock, args[1], args[2])
    elif command == 'd':
        sock.send(int32_to_web(CMD_DELETE_FILE))
        delete_file(sock, args[1])
    elif command == 'n':
        sock.send(int32_to_web(CMD_CREATE_EMPTY_FILE))
        create_empty_file(sock, args[1])
    elif command == 'i':
        sock.send(int32_to_web(CMD_FILE_INFO))
        get_file_info(sock, args[1])


def main():
    while True:
        args = input('Enter command:').split()
        try:
            send_command_to_storage_server('localhost', args)
        except Exception as e:
            print(str(e))


if __name__ == "__main__":
    main()
