import socket
import shutil
from pathlib import Path

from constants import *
from naming_server_client import send_command_to_naming_server
from status_codes import *
from receiver import *
from sender import *
from storage_server_client import send_command_to_storage_server
from super_client_directories import *


def open_socket(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((ip, port))
    return sock


def init_server(sock):
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

    reset_path()

    print('Initalization complete. You have ' + str(INITIAL_SIZE) + ' MBs available.')


def create_file(file_name: str):
    file_path = os.path.join(CLIENT_ROOT_PATH, file_name)
    Path(file_path).touch()

    if not write_file(file_name):
        print("error when creating an empty file on server")
        return False

    print('created empty file')
    return True


def write_file(file_name: str):
    storage = send_command_to_naming_server(CMD_GET_STORAGE, [])

    file_id = send_command_to_naming_server(CMD_WRITE_FILE, [file_name])
    if file_id is None or file_id is False:
        print('error: file_id is %s' % file_id)
        return False

    storage_index = 0
    while True:
        if send_command_to_storage_server(storage[storage_index], CMD_WRITE_FILE,
                                          [file_name, file_id, CLIENT_ROOT_PATH]):
            break
        storage_index += 1
        if storage_index == len(storage):
            storage_index = 0
            storage = send_command_to_naming_server(CMD_GET_STORAGE, [])
            if storage is None:
                print('error: storage server is None')
                return False
    return True


def read_file(file_name: str):
    storage = send_command_to_naming_server(CMD_GET_STORAGE, [])

    file_id = send_command_to_naming_server(CMD_READ_FILE, [file_name])
    if file_id is None:
        print('error: file_id is None')
        return

    storage_index = 0
    while True:
        if send_command_to_storage_server(storage[storage_index], CMD_READ_FILE, [file_id, file_name]):
            break
        storage_index += 1
        if storage_index == len(storage):
            storage_index = 0
            storage = send_command_to_naming_server(CMD_GET_STORAGE, [])
            if storage is None:
                print('error: storage server is None')


def copy_file(old_file_name: str, new_file_name: str):
    if not send_command_to_naming_server(CMD_COPY_FILE, [old_file_name, new_file_name]):
        print('error while copying the file')
        return
    shutil.copy(os.path.join(CLIENT_ROOT_PATH, old_file_name), os.path.join(CLIENT_ROOT_PATH, new_file_name))


def delete_file(file_name: str):
    if not send_command_to_naming_server(CMD_DELETE_FILE, [file_name]):
        print('error while removing a file')
    print('file removed')


def file_info(sock, file_name):
    send_int32(sock, CMD_FILE_INFO)
    send_str(sock, file_name)
    ret = receive_str(sock)
    print('info response: ' + ret)


def move_file(sock, file_name, new_dir):
    send_int32(sock, CMD_FILE_MOVE)
    file_path = storage_path_plus() + file_name
    if new_dir == 'root': new_dir = ''
    send_str(sock, file_path)
    send_str(sock, new_dir)
    ret = receive_str(sock)
    if ret == str(CODE_OK):
        new_path = CLIENT_ROOT_PATH + '/' + new_dir + '/' + file_name
        if new_dir == '': new_path = CLIENT_ROOT_PATH + '/' + file_name
        try:
            shutil.move(path_plus() + file_name, new_path)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))
    print('mv response: ' + ret)


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
        elif cmd == 'touch' and len(args) == 1:
            create_file(args[0])
        elif cmd == 'w' and len(args) == 1:
            write_file(args[0])
        elif cmd == 'r' and len(args) == 1:
            read_file(args[0])
        elif cmd == 'cp' and len(args) == 2:
            copy_file(args[0], args[1])
        elif cmd == 'info' and len(args) == 1:
            file_info(naming_server_sock, args[0])
        elif cmd == 'mv' and len(args) == 2:
            move_file(naming_server_sock, args[0], args[1])
        elif cmd == 'rm' and len(args) == 1:
            delete_file(args[0])
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
