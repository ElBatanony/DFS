import os
import socket

from constants import STORAGE_SERVER_PORT, CLIENT_ROOT_PATH
from receiver import receive_file, receive_str, receive_int32
from sender import send_str, send_file
from status_codes import CMD_WRITE_FILE, CMD_READ_FILE, CODE_OK, CMD_CREATE_EMPTY_FILE, CMD_DELETE_FILE, \
    CMD_FILE_INFO, CMD_COPY_FILE
from web_format_converter import int32_to_web, web_to_int


def get_file_info(sock, file_name):
    sock.send(int32_to_web(CMD_FILE_INFO))
    send_str(sock, file_name)
    code = web_to_int(sock.recv(32))
    if code != CODE_OK:
        raise Exception('error with code %d' % code)
    file_info = receive_str(sock)
    print(file_info)


def create_empty_file(sock, file_name):
    sock.send(int32_to_web(CMD_CREATE_EMPTY_FILE))
    send_str(sock, file_name)
    code = web_to_int(sock.recv(32))
    if code != CODE_OK:
        raise Exception('error with code %d' % code)
    else:
        print('file created')


def delete_file(sock, file_name):
    sock.send(int32_to_web(CMD_DELETE_FILE))
    send_str(sock, file_name)
    code = web_to_int(sock.recv(32))
    if code != CODE_OK:
        raise Exception('error with code %d' % code)
    else:
        print('file removed')


def copy_file(sock, old_file_name, new_file_name):
    sock.send(int32_to_web(CMD_COPY_FILE))
    send_str(sock, old_file_name)
    send_str(sock, new_file_name)
    code = web_to_int(sock.recv(32))
    if code != CODE_OK:
        raise Exception('error with code %d' % code)
    else:
        print('file copied')


def read_file(sock, file_name):
    sock.send(int32_to_web(CMD_READ_FILE))
    send_str(sock, file_name)
    code = web_to_int(sock.recv(32))
    if code != CODE_OK:
        raise Exception('error with code %d' % code)
    receive_file(sock, file_name, CLIENT_ROOT_PATH)


def write_file(sock, path_to_source_file, path_to_destination_file):
    if not os.path.exists(os.path.join(CLIENT_ROOT_PATH, path_to_source_file)):
        raise Exception('file does not exist')
    sock.send(int32_to_web(CMD_WRITE_FILE))
    send_str(sock, path_to_destination_file)
    send_file(sock, path_to_source_file, CLIENT_ROOT_PATH)
    try:
        code = receive_int32(sock)
    except Exception as e:
        print(str(e))
        return False
    if code != CODE_OK:
        print('error with code %d' % str(code))
        return False
    return True


def send_command_to_storage_server(host, cmd, args=[]):
    port = STORAGE_SERVER_PORT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, port))

    result = None

    if cmd == 'w' and len(args) == 2:
        result = write_file(sock, args[0], args[1])
    elif cmd == 'r' and len(args) == 1:
        result = read_file(sock, args[0])
    elif cmd == 'c' and len(args) == 2:
        result = copy_file(sock, args[0], args[1])
    elif cmd == 'd' and len(args) == 1:
        result = delete_file(sock, args[0])
    elif cmd == 'n' and len(args) == 1:
        result = create_empty_file(sock, args[0])
    elif cmd == 'i' and len(args) == 1:
        result = get_file_info(sock, args[0])
    else:
        print('unrecognized command')

    sock.close()
    return result


def main():
    while True:
        args = input('Enter command:').split()
        try:
            send_command_to_storage_server('localhost', args[0], args[1:])
        except Exception as e:
            print(str(e))


if __name__ == "__main__":
    main()
