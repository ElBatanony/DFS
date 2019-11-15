import json
import socket
import uuid
from threading import Thread
from status_codes import *
from receiver import *
from sender import *
from constants import *

clients = []

directories = {}

available_storage_servers = []

class Directory:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def __init__(self, path):
        self.path = path
        self.directories = []
        self.files = {}


class File:
    def __init__(self, name: str, size: int):
        self.name = name
        self.size = size
        self.id = str(uuid.uuid4())
        self.storage = ['ip1', 'ip2', 'ip3']


def get_prev(path):
    return '/'.join(path.split('/')[:-1])

def get_last(path):
    return path.split('/')[-1]

def get_directory_from_full_file_name(file_name):
    if len(file_name.split('/')) == 1:
        return ''
    return get_prev(file_name)

def delete_file_by_path(file_path):
    return

''' Yet another section '''

def storage_available(ip,port):
    # ping storage server
    return True

''' Another section '''

def initialize():
    delete_directory(STORAGE_ROOT_PATH, True)
    directories[STORAGE_ROOT_PATH] = Directory(STORAGE_ROOT_PATH)
    return CODE_OK

def create_file(file_path):
    return

def file_info(file_path):
    file_dir = get_prev(file_path)
    file_name = get_last(file_path)
    if file_dir in directories:
        if file_name in directories[file_dir].files:
            f = directories[file_dir].files[file_name]
            ret = '{},{},{},{},{},{}'.format(f.name, f.id, str(
                f.size), f.storage[0], f.storage[1], f.storage[2])
            return ret
        else:
            return ERR_FILE_NOT_EXIST
    else:
        return ERR_FILE_DIR_NOT_EXIST


def move_file_by_path(file_path, new_path):
    return 'NOT IMPLEMENTED YET. WAITING FOR FILES.'


''' Directory Functions '''

def check_directory(directory_path):
    if directory_path in directories:
        return CODE_OK
    else:
        return CODE_DIRECTORY_NOT_EXIST

def read_directory(directory_path):
    if directory_path in directories:
        ret = ' '
        for dir in directories[directory_path].directories:
            ret += dir + '/ '
        for file in directories[directory_path].files.keys():
            ret += file + ' '
        return ret
    else:
        return CODE_DIRECTORY_NOT_EXIST

def make_directory(directory_path):
    if directory_path in directories:
        return CODE_DIRECTORY_ALREADY_EXIST
    directories[directory_path] = Directory(directory_path)
    directory_name = get_last(directory_path)
    directories[get_prev(directory_path)].directories.append(directory_name)
    return DIR_MAKE_OK

def delete_directory(directory_path, force):
    if directory_path in directories:
        dir_files = directories[directory_path].files
        dir_dir = directories[directory_path].directories

        if not force:
            if dir_files or dir_dir:
                return DIR_DELETE_HAS_FILES

        for file in dir_files:
            delete_file_by_path(directory_path + '/' + file)
        for dir in dir_dir:
            delete_directory(directory_path + '/' + dir, True)

        directory_name = directory_path.split('/')[-1]
        #if get_prev(directory_path) != '':
        directories[get_prev(directory_path)].directories.remove(
                directory_name)
        del directories[directory_path]

        return DIR_DELETE_OK
    else:
        return DIR_DELETE_NOT_EXIST


class ClientListener(Thread):

    def __init__(self, name: str, sock: socket.socket):
        super().__init__(daemon=True)
        self.sock = sock
        self.name = name
        self.path = name
        directories[''] = Directory('')

    def _close(self):
        clients.remove(self.sock)
        self.sock.close()
        print(self.name + ' disconnected')

    ''' Files Section '''

    def write_file(self):
        try:
            full_file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            return

        try:
            file_size = receive_int64(self.sock)
        except Exception as e:
            print(str(e))
            return

        path_to_file = get_directory_from_full_file_name(full_file_name)

        if path_to_file not in directories:
            send_int32(self.sock, CODE_DIRECTORY_NOT_EXIST)
            return

        directory = directories[path_to_file]
        file_name = get_last(full_file_name)

        if file_name in directory.files:
            file = directory.files[file_name]
        else:
            file = File(name, file_size)
            directory.files[file_name] = file

        send_int32(self.sock, CODE_OK)
        send_str(self.sock, file.id)
        send_int32(self.sock, len(file.storage))
        for i in range(len(file.storage)):
            send_str(self.sock, file.storage[i])

    def read_file(self):
        try:
            full_file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            return

        path_to_file = get_directory_from_full_file_name(full_file_name)

        if path_to_file not in directories:
            send_int32(self.sock, CODE_DIRECTORY_NOT_EXIST)
            return

        directory = directories[path_to_file]
        file_name = get_last(full_file_name)

        if file_name not in directory.files:
            send_int32(self.sock, CODE_FILE_NOT_EXIST)
            return

        file = directory.files[file_name]

        send_int32(self.sock, CODE_OK)
        send_str(self.sock, file.id)
        send_int32(self.sock, len(file.storage))
        for i in range(len(file.storage)):
            send_str(self.sock, file.storage[i])

    def delete_file(self, file_name):
        return delete_file_by_path(self.path + '/' + file_name)

    ''' Directories Section '''

    def move_file(self, file_name, new_path):
        return move_file_by_path(self.path + '/' + file_name, new_path)

    def run(self):
        while True:
            try:
                cmd = web_to_int(self.sock.recv(32))
            except Exception as e:
                print(str(e))
                self._close()
                return

            if cmd == CMD_INIT:
                ret = initialize()
                send_str(self.sock, ret)

            # elif cmd == CMD_CREATE_EMPTY_FILE:
            #     file_path = receive_str(self.sock)
            #     ret = create_file(file_path)
            #     send_str(self.sock, ret)
            # if cmd == CMD_WRITE_FILE:
            #     self.write_file()
            # elif cmd == CMD_READ_FILE:
            #     self.read_file()
            # elif cmd == CMD_FILE_INFO:
            #     file_path = receive_str(self.sock)
            #     ret = file_info(file_path)
            #     send_str(self.sock, ret)
            # elif cmd == CMD_FILE_MOVE:
            #     file_name = receive_str(self.sock)
            #     new_path = receive_str(self.sock)
            #     ret = self.move_file(file_name, new_path)
            #     send_str(self.sock, ret)

            elif cmd == CMD_CHECK_DIR:
                directory_path = receive_str(self.sock)
                ret = check_directory(directory_path)
                send_str(self.sock, ret)
            elif cmd == CMD_READ_DIR:
                directory_path = receive_str(self.sock)
                ret = read_directory(directory_path)
                send_str(self.sock, ret)
            elif cmd == CMD_MAKE_DIR:
                directory_path = receive_str(self.sock)
                ret = make_directory(directory_path)
                send_str(self.sock, ret)
            elif cmd == CMD_DELETE_DIR:
                directory_path = receive_str(self.sock)
                force = receive_str(self.sock)
                ret = delete_directory(directory_path, force)
                send_str(self.sock, ret)

            elif cmd == CMD_CLOSE_SOCK:
                break
            else:
                print('Error reading command code.')

        self._close()


if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 8800))
    sock.listen()

    while True:
        print('naming server listening for client')

        con, addr = sock.accept()
        clients.append(con)
        name = 'da_client'
        print(name + ' connected from ' + str(addr[0]))
        clientListener = ClientListener(name, con)
        clientListener.start()
