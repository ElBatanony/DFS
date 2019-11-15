import socket
import shutil
from pathlib import Path

from constants import *
from naming_server_client import send_command_to_naming_server
from status_codes import *
from receiver import *
from sender import *
from storage_server_client import send_command_to_storage_server

path = CLIENT_ROOT_PATH


def get_prev(path): return '/'.join(path.split('/')[:-1])


def get_last(path): return path.split('/')[-1]


def open_socket(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((ip, port))
    return sock


def storage_path():
    return '/'.join(path.split('/')[1:])


def storage_path_plus():
    sp = storage_path()
    if sp != '': return sp + '/'
    return sp


def path_plus():
    if path != '': return path + '/'
    return path


def init_server(sock):
    global path

    # Send initialize command to naming server
    send_int32(sock, CMD_INIT)
    # Receive confirmation that it was completed
    ret = receive_str(sock)

    if ret != str(CODE_OK):
        print("Error with initalizing on server. Error: " + ret)
        return

    # Delete local dfs and all its content
    try:
        shutil.rmtree(CLIENT_ROOT_PATH)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))

    # Recreate the local dfs directory
    try:
        os.mkdir(CLIENT_ROOT_PATH)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))

    path = CLIENT_ROOT_PATH

    print('Initalization complete. You have ' + str(INITIAL_SIZE) + ' MBs available.')


def create_file(sock, file_name: str):
    file_path = path + '/' + file_name

    Path(file_path).touch()

    ret = write_file(file_name)
    if ret != CODE_OK:
        print("Error with creating an empty file on server. Error: " + ret)

    print('Created empty file')
    return ret


def read_file(sock: socket.socket, file_name: str):
    return CODE_OK


def write_file(file_name: str):
    storage = send_command_to_naming_server(CMD_GET_STORAGE, [])

    file_id = send_command_to_naming_server(CMD_WRITE_FILE, [file_name])
    if file_id is None:
        print('error: file_id is None')
        return

    storage_index = 0
    while True:
        if send_command_to_storage_server(storage[storage_index], CMD_WRITE_FILE, [file_name, file_id]):
            break
        storage_index += 1
        if storage_index == len(storage):
            storage_index = 0
            storage = send_command_to_naming_server(CMD_GET_STORAGE, [])
            if storage is None:
                print('error: storage server is None')


def delete_file(sock: socket.socket, file_name: str):
    return CODE_OK


def file_info(sock, file_name):
    send_int32(sock, CMD_FILE_INFO)
    send_str(sock, file_name)
    ret = receive_str(sock)
    print('info response: ' + ret)


def copy_file(sock, file_name):
    return


def move_file(sock, file_name, new_path):
    send_int32(sock, CMD_FILE_MOVE)
    send_str(sock, file_name)
    send_str(sock, new_path)
    ret = receive_str(sock)
    print('mv response: ' + ret)


def open_directory(sock, directory_name):
    global path

    if directory_name == '..':
        if path == STORAGE_SERVER_ROOT_PATH:
            return DIR_OPEN_ROOT
        path = get_prev(path)
        return DIR_OPEN_PREV

    send_int32(sock, CMD_CHECK_DIR)
    send_str(sock, storage_path_plus() + directory_name)
    dir_exists = receive_str(sock)

    if dir_exists != str(CODE_OK):
        print('Directory does not exist. Error: ' + dir_exists)
        return DIR_OPEN_NOT_EXIST

    path = path_plus() + directory_name

    if not os.path.isdir(path):
        os.mkdir(path)

    return DIR_OPEN_OK


def read_directory(sock):
    # make sure that directory exists on machine
    send_int32(sock, CMD_READ_DIR)
    send_str(sock, storage_path())

    dir = receive_str(sock)
    print('ls response: ' + dir)


def make_directory(sock, directory_name):
    # make sure that directory exists on machine
    send_int32(sock, CMD_MAKE_DIR)
    directory_path = storage_path_plus() + directory_name
    send_str(sock, directory_path)
    ret = receive_str(sock)
    if not os.path.isdir(path_plus() + directory_name):
        os.mkdir(path_plus() + directory_name)
    print('mkdir response: ' + ret)


def delete_directory(sock, directory_name, force=False):
    # make sure that directory exists on machine
    send_int32(sock, CMD_DELETE_DIR)
    directory_path = storage_path_plus() + directory_name
    send_str(sock, directory_path)
    send_str(sock, force)
    ret = receive_str(sock)
    try:
        shutil.rmtree(path_plus() + directory_name)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    print('rmdir response: ' + ret)


def main():
    if not os.path.isdir(CLIENT_ROOT_PATH):
        os.mkdir(CLIENT_ROOT_PATH)

    cmd = ''
    while True:

        if cmd == 'exit':
            print('Exiting')
            break

        naming_server_sock = open_socket(
            NAMING_SERVER_IP, int(NAMING_SERVER_PORT))
        inp = input('Enter command: ')
        cmd = inp.split(' ')[0]
        args = inp.split(' ')[1:]

        if cmd == 'init' and len(args) == 0:
            init_server(naming_server_sock)
        # elif cmd == 'touch' and len(args) == 1:
        #     create_file(naming_server_sock, args[0])
        # elif cmd == 'r' and len(args) == 1:
        #     read_file(naming_server_sock, args[0])
        elif cmd == 'w' and len(args) == 1:
            write_file(args[0])
        # elif cmd == 'del' and len(args) == 1:
        #     delete_file(sock, args[0])
        # elif cmd == 'info' and len(args) == 1:
        #     file_info(naming_server_sock, args[0])
        # elif cmd == 'copy' and len(args) == 1:
        #     copy_file(sock, args[0])
        # elif cmd == 'mv' and len(args) == 2:
        #     move_file(sock, args[0], args[1])

        elif cmd == 'cd' and len(args) == 1:
            open_directory(naming_server_sock, args[0])
        elif cmd == 'ls' and len(args) == 0:
            read_directory(naming_server_sock)
        elif cmd == 'mkdir' and len(args) == 1:
            make_directory(naming_server_sock, args[0])
        elif cmd == 'rmdir' and len(args) == 1:
            delete_directory(naming_server_sock, args[0])
        elif cmd == 'rmdir' and len(args) == 2:
            delete_directory(naming_server_sock, args[0], args[1])
        else:
            print('Command-arguments combination unrecognized')

        naming_server_sock.send(int32_to_web(CMD_CLOSE_SOCK))
        naming_server_sock.close()


if __name__ == "__main__":
    main()
