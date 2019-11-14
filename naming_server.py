import json
import socket
import uuid
from threading import Thread
from status_codes import *
from receiver import *
from sender import *
from constants import *
from storage_server_client import send_command_to_storage_server

clients = []

storage = ['localhost', 'localhost', 'localhost']

directories = {}

write_file_map = {}


class Directory:
    def __init__(self, path):
        self.path = path
        self.directories = []
        self.files = {}


class File:
    def __init__(self, name: str, size: int):
        self.name = name
        self.size = size
        self.id = str(uuid.uuid4())


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


''' Directory Functions '''


def make_directory_by_path(directory_path):
    if directory_path in directories:
        return DIR_MAKE_EXISTS
    directories[directory_path] = Directory(directory_path)
    directory_name = get_last(directory_path)
    directories[get_prev(directory_path)].directories.append(directory_name)
    return DIR_MAKE_OK


def delete_directory_by_path(directory_path, force):
    if directory_path in directories:
        dir_files = directories[directory_path].files
        dir_dir = directories[directory_path].directories

        if not force:
            if dir_files or dir_dir:
                return DIR_DELETE_HAS_FILES

        for file in dir_files:
            delete_file_by_path(directory_path + '/' + file)
        for dir in dir_dir:
            delete_directory_by_path(directory_path + '/' + dir, True)

        directory_name = directory_path.split('/')[-1]
        if get_prev(directory_path) != '': directories[get_prev(directory_path)].directories.remove(directory_name)
        del directories[directory_path]

        return DIR_DELETE_OK
    else:
        return DIR_DELETE_NOT_EXIST


def file_info_by_path(file_path):
    file_dir = get_prev(file_path)
    file_name = get_last(file_path)
    if file_dir in directories:
        if file_name in directories[file_dir].files:
            f = directories[file_dir].files[file_name]
            ret = '{},{},{},{},{},{}'.format(f.name, f.id, str(f.size), f.storage[0], f.storage[1], f.storage[2])
            return ret
        else:
            return ERR_FILE_NOT_EXIST
    else:
        return ERR_FILE_DIR_NOT_EXIST


def move_file_by_path(file_path, new_path):
    return 'NOT IMPLEMENTED YET. WAITING FOR FILES.'


class ClientListener(Thread):

    def __init__(self, name: str, sock: socket.socket):
        super().__init__(daemon=True)
        self.sock = sock
        self.name = name
        self.path = name

    def _close(self):
        clients.remove(self.sock)
        self.sock.close()
        print(self.name + ' disconnected')

    def get_storage(self):
        send_int32(self.sock, len(storage))
        for i in range(len(storage)):
            send_str(self.sock, storage[i])

    ''' Files Section '''

    def confirm_file_upload(self):
        try:
            file_id = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            return

        if file_id not in write_file_map:
            return

        file, directory = write_file_map[file_id]
        directory.files[file.name] = file
        del write_file_map[file_id]

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
            file = File(file_name, file_size)
            write_file_map[file.id] = file, directory

        send_int32(self.sock, CODE_OK)
        send_str(self.sock, file.id)

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

    def copy_file(self):
        try:
            full_source_file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            return

        try:
            full_destination_file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            return

        path_to_source_file = get_directory_from_full_file_name(full_source_file_name)
        path_to_destination_file = get_directory_from_full_file_name(full_destination_file_name)

        if path_to_source_file not in directories or path_to_destination_file not in directories:
            send_int32(sock, CODE_DIRECTORY_NOT_EXIST)
            return

        source_directory = directories[path_to_source_file]
        destination_directory = directories[path_to_source_file]

        source_file_name = get_last(full_source_file_name)
        destination_file_name = get_last(full_destination_file_name)

        if source_file_name not in source_directory.files:
            send_int32(sock, CODE_FILE_NOT_EXIST)

        source_file = source_directory.files[source_file_name]

        if destination_file_name in destination_directory.files:
            destination_file = destination_directory.files[destination_file_name]
        else:
            destination_file = File(destination_file_name, source_file.size)
            destination_directory.files[destination_file_name] = destination_file

        storage_index = 0
        while True:
            try:
                send_command_to_storage_server(source_file.storage[storage_index],
                                               ['c', source_file.id, destination_file.id])
                break
            except Exception as e:
                print(str(e))
                storage_index += 1

        send_int32(sock, CODE_OK)

    def delete_file(self, file_name):
        return delete_file_by_path(self.path + '/' + file_name)

    ''' Directories Section '''

    def open_directory(self, directory_name):
        if directory_name == '..':
            if self.name == self.path:
                return DIR_OPEN_ROOT
            self.path = get_prev(self.path)
            return DIR_OPEN_PREV
        if self.path + '/' + directory_name in directories:
            self.path = self.path + '/' + directory_name
            return DIR_OPEN_OK
        return DIR_OPEN_NOT_EXIST

    def read_directory(self):
        ret = ' '
        for dir in directories[self.path].directories:
            ret += dir + '/ '
        for file in directories[self.path].files.keys():
            ret += file + ' '
        return ret

    def make_directory(self, directory_name):
        return make_directory_by_path(self.path + '/' + directory_name)

    def delete_directory(self, directory_name, force=False):
        return delete_directory_by_path(self.path + '/' + directory_name, force)

    def file_info(self, file_name):
        return file_info_by_path(self.path + '/' + file_name)

    def move_file(self, file_name, new_path):
        return move_file_by_path(self.path + '/' + file_name, new_path)

    def run(self):
        try:
            cmd = web_to_int(self.sock.recv(32))
        except Exception as e:
            print(str(e))
            self._close()
            return

        if cmd == CMD_CONFIRM_FILE_UPLOAD:
            self.confirm_file_upload()
        elif cmd == CMD_GET_STORAGE:
            self.get_storage()
        elif cmd == CMD_WRITE_FILE:
            self.write_file()
        elif cmd == CMD_READ_FILE:
            self.read_file()
        elif cmd == CMD_COPY_FILE:
            self.copy_file()
        elif cmd == CMD_OPEN_DIR:
            directory_name = receive_str(self.sock)
            ret = self.open_directory(directory_name)
            send_str(self.sock, ret)
        elif cmd == CMD_READ_DIR:
            ret = self.read_directory()
            send_str(self.sock, ret)
        elif cmd == CMD_MAKE_DIR:
            directory_name = receive_str(self.sock)
            ret = self.make_directory(directory_name)
            send_str(self.sock, ret)
        elif cmd == CMD_DELETE_DIR:
            directory_name = receive_str(self.sock)
            ret = self.delete_directory(directory_name)
            send_str(self.sock, ret)
        elif cmd == CMD_INIT:
            self.path = self.name
            delete_directory_by_path(self.name, True)
            directories[self.name] = Directory(self.name)
            send_str(self.sock, 'Storage initialized. You have ' + str(INITIAL_SIZE) + ' MBs available.')
        elif cmd == CMD_FILE_INFO:
            file_name = receive_str(self.sock)
            ret = self.file_info(file_name)
            send_str(self.sock, ret)
        elif cmd == CMD_FILE_MOVE:
            file_name = receive_str(self.sock)
            new_path = receive_str(self.sock)
            ret = self.move_file(file_name, new_path)
            send_str(self.sock, ret)
        else:
            print('Error reading command code.')

        self._close()


if __name__ == "__main__":
    directories[''] = Directory('')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', NAMING_SERVER_PORT))
    sock.listen()

    while True:
        print('naming server listening for client')

        con, addr = sock.accept()
        clients.append(con)
        name = 'da_client'
        print(name + ' connected from ' + str(addr[0]))
        clientListener = ClientListener(name, con)
        clientListener.start()
