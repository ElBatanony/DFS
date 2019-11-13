import socket

from constants import *
from status_codes import *
from receiver import *
from sender import *


def write_file(sock, file_name):
    if not os.path.exists(CLIENT_ROOT_PATH + file_name):
        print('error: file does not exist')
        return

    send_int32(sock, CMD_WRITE_FILE)
    send_str(sock, file_name)
    send_int64(sock, os.path.getsize(file_name))

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

    try:
        storage_size = receive_int32(sock)
    except Exception as e:
        print(str(e))
        return

    storage = []

    for i in range(storage_size):
        try:
            s = receive_str(sock)
            storage.append(s)
        except Exception as e:
            print(str(e))
            return

    print(file_id)
    print(str(storage))


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

    try:
        storage_size = receive_int32(sock)
    except Exception as e:
        print(str(e))
        return

    storage = []

    for i in range(storage_size):
        try:
            s = receive_str(sock)
            storage.append(s)
        except Exception as e:
            print(str(e))
            return

    print(file_id)
    print(str(storage))


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


def main():
    # host = sys.argv[len(sys.argv) - 2]
    # port = int(sys.argv[len(sys.argv) - 1])
    host = 'localhost'
    port = 8800

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, port))

    cmd = ''
    while True:
        inp = input('Enter command: ')
        cmd = inp.split(' ')[0]
        args = inp.split(' ')[1:]

        if cmd == 'w' and len(args) == 1:
            write_file(sock, args[0])
        elif cmd == 'r' and len(args) == 1:
            read_file(sock, args[0])
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
        elif cmd == 'exit':
            print('Exiting')
            break
        else:
            print('Command-arguments combination unrecognized')

    sock.send(int32_to_web(CMD_CLOSE_SOCK))
    sock.close()


if __name__ == "__main__":
    main()
