import socket

from constants import *
from status_codes import *
from receiver import *
from sender import *

storage = []


def confirm_file_upload(sock, file_id):
    send_int32(sock, CMD_CONFIRM_FILE_UPLOAD)
    send_str(sock, file_id)


def get_storage(sock):
    global storage
    send_int32(sock, CMD_GET_STORAGE)
    size = receive_int32(sock)
    new_storage = []
    for i in range(size):
        new_storage.append(receive_str(sock))
    storage = new_storage
    print(str(storage))


def write_file(sock, file_name):
    if not os.path.exists(CLIENT_ROOT_PATH + file_name):
        print('error: file does not exist')
        return

    send_int32(sock, CMD_WRITE_FILE)
    send_str(sock, file_name)
    send_int64(sock, os.path.getsize(CLIENT_ROOT_PATH + file_name))

    try:
        code = receive_int32(sock)
    except Exception as e:
        print(str(e))
        return

    if code != CODE_OK:
        print('error with code %d' % code)
        return

    try:
        file_id = receive_str(sock)
    except Exception as e:
        print(str(e))
        return

    print(file_id)


def read_file(sock, file_name):
    if not os.path.exists(CLIENT_ROOT_PATH + file_name):
        print('error: file does not exist')
        return

    send_int32(sock, CMD_READ_FILE)
    send_str(sock, file_name)

    try:
        code = receive_int32(sock)
    except Exception as e:
        print(str(e))
        return

    if code != CODE_OK:
        print('error with code %d' % code)
        return

    try:
        file_id = receive_str(sock)
    except Exception as e:
        print(str(e))
        return

    print(file_id)


def copy_file(sock, source_file_name, destination_file_name):
    send_int32(sock, CMD_COPY_FILE)
    send_str(sock, source_file_name)
    send_str(sock, destination_file_name)
    code = receive_int32(sock)
    if code != CODE_OK:
        print('error with code %d' % code)
        return
    print('file copied')


def open_directory(sock, directory_name):
    send_int32(sock, CMD_OPEN_DIR)
    send_str(sock, directory_name)
    ret = receive_str(sock)
    print('cd response: ' + ret)


def read_directory(sock):
    send_int32(sock, CMD_READ_DIR)
    dir = receive_str(sock)
    print('ls response: ' + dir)


def make_directory(sock, directory_name):
    send_int32(sock, CMD_MAKE_DIR)
    send_str(sock, directory_name)
    ret = receive_str(sock)
    print('mkdir response: ' + ret)


def delete_directory(sock, directory_name):
    send_int32(sock, CMD_DELETE_DIR)
    send_str(sock, directory_name)
    ret = receive_str(sock)
    print('rmdir response: ' + ret)


def init_server(sock):
    send_int32(sock, CMD_INIT)
    ret = receive_str(sock)
    print('init response: ' + ret)


def file_info(sock, file_name):
    send_int32(sock, CMD_FILE_INFO)
    send_str(sock, file_name)
    ret = receive_str(sock)
    print('info response: ' + ret)


def move_file(sock, file_name, new_path):
    send_int32(sock, CMD_FILE_MOVE)
    send_str(sock, file_name)
    send_str(sock, new_path)
    ret = receive_str(sock)
    print('mv response: ' + ret)


def send_command_to_naming_server(cmd, args):
    host = 'localhost'
    port = NAMING_SERVER_PORT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, port))

    if cmd == 'cf' and len(args) == 1:
        confirm_file_upload(sock, args[0])
    elif cmd == 's' and len(args) == 0:
        get_storage(sock)
    elif cmd == 'w' and len(args) == 1:
        write_file(sock, args[0])
    elif cmd == 'r' and len(args) == 1:
        read_file(sock, args[0])
    elif cmd == 'c' and len(args) == 2:
        copy_file(sock, args[0], args[1])
    elif cmd == 'cd' and len(args) == 1:
        open_directory(sock, args[0])
    elif cmd == 'ls' and len(args) == 0:
        read_directory(sock)
    elif cmd == 'mkdir' and len(args) == 1:
        make_directory(sock, args[0])
    elif cmd == 'rmdir' and len(args) == 1:
        delete_directory(sock, args[0])
    elif cmd == 'init' and len(args) == 0:
        init_server(sock)
    elif cmd == 'info' and len(args) == 1:
        file_info(sock, args[0])
    elif cmd == 'mv' and len(args) == 2:
        move_file(sock, args[0], args[1])
    else:
        print('Command-arguments combination unrecognized')

    sock.close()


def main():
    while True:
        inp = input('Enter command: ')
        cmd = inp.split(' ')[0]
        if cmd == 'exit':
            break
        args = inp.split(' ')[1:]
        send_command_to_naming_server(cmd, args)


if __name__ == "__main__":
    main()
