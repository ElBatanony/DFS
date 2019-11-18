import socket
import uuid
from threading import Thread
from status_codes import *
from receiver import *
from sender import *
from constants import *
from storage_server_client import send_command_to_storage_server
from naming_server_directories import *
import threading
import time

clients = []

storage = []

write_file_map = {}


class File:
    def __init__(self, name: str, size: int):
        self.name = name
        self.size = size
        self.id = str(uuid.uuid4())

def ping_storages():
    while True:
        print('pinging storages')
        for st in storage:
            if not send_command_to_storage_server( st , CMD_PING_AS_NAMING, [] ) :
                print('lost ' + st)
                storage.remove(st)
        time.sleep(PING_SERVERS_SECONDS)

def get_directory_from_full_file_name(file_name):
    if len(file_name.split('/')) == 1:
        return ''
    return get_prev(file_name)


def initialize():
    delete_directory('', True)
    reset_directories()
    return CODE_OK


def file_info(file_path):
    file_dir = get_prev(file_path)
    file_name = get_last(file_path)
    if file_dir in directories:
        if file_name in directories[file_dir].files:
            f = directories[file_dir].files[file_name]
            ret = 'name: {}, size{} bytes, id: {}'.format(f.name, str(f.size), f.id)
            return ret
        else:
            return ERR_FILE_NOT_EXIST
    else:
        return ERR_FILE_DIR_NOT_EXIST


def move_file(file_path, new_dir):
    file_dir = get_prev(file_path)
    file_name = get_last(file_path)
    if file_dir in directories:
        if file_name in directories[file_dir].files:
            if not (new_dir in directories):
                return ERR_DIR_NOT_EXIST
            directories[new_dir].files[file_name] = directories[file_dir].files[file_name]
            del directories[file_dir].files[file_name]
            return CODE_OK
        else:
            return ERR_FILE_NOT_EXIST
    else:
        return ERR_FILE_DIR_NOT_EXIST


class ClientListener(Thread):

    def __init__(self, name: str, sock: socket.socket, address):
        super().__init__(daemon=True)
        self.sock = sock
        self.name = name
        self.path = name
        self.address = address

    def _close(self):
        clients.remove(self.sock)
        self.sock.close()
        # print(self.name + ' disconnected')

    def get_storage(self):
        send_int32(self.sock, len(storage))
        for i in range(len(storage)):
            send_str(self.sock, storage[i])

    def ping_as_storage(self):
        try:
            code = receive_int32(self.sock)
        except Exception as e:
            print(str(e))
            return

        if code != CODE_OK:
            print('error with code %d' % code)
            return

        send_int32(self.sock, CODE_OK)

        for dir in directories.values():
            for f in dir.files.values():
                send_command_to_storage_server(self.address, CMD_REPLICATE_FILE, [storage[0], f.id])

        storage.append(self.address)
        print('%s storage connected' % self.address)

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
        print('file "%s" confirmed' % file.name)

        for s in storage:
            if s != self.address:
                send_command_to_storage_server(s, CMD_REPLICATE_FILE, [self.address, file.id])

        send_int32(self.sock, CODE_OK)

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
                send_command_to_storage_server(storage[storage_index], CMD_COPY_FILE,
                                               [source_file.id, destination_file.id])
                break
            except Exception as e:
                print(str(e))
                storage_index += 1
                if storage_index >= len(storage):
                    storage_index = 0

        send_int32(self.sock, CODE_OK)

    def run(self):
        try:
            cmd = web_to_int(self.sock.recv(32))
        except Exception as e:
            print(str(e))
            self._close()
            return

        print("Received " + str(cmd) + " from " + self.name)

        if cmd == CMD_INIT:
            ret = initialize()
            send_str(self.sock, ret)
        elif cmd == CMD_PING_AS_STORAGE:
            self.ping_as_storage()
        elif cmd == CMD_GET_STORAGE:
            self.get_storage()
        elif cmd == CMD_WRITE_FILE:
            self.write_file()
        elif cmd == CMD_READ_FILE:
            self.read_file()
        elif cmd == CMD_COPY_FILE:
            self.copy_file()
        elif cmd == CMD_CONFIRM_FILE_UPLOAD:
            self.confirm_file_upload()
        elif cmd == CMD_FILE_INFO:
            file_path = receive_str(self.sock)
            ret = file_info(file_path)
            send_str(self.sock, ret)
        elif cmd == CMD_FILE_MOVE:
            file_path = receive_str(self.sock)
            new_dir = receive_str(self.sock)
            ret = move_file(file_path, new_dir)
            send_str(self.sock, ret)
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
        else:
            print('error reading command code')

        self._close()


if __name__ == "__main__":
    directories[''] = Directory('')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', NAMING_SERVER_PORT))
    sock.listen()
    # sock.settimeout(10) # for debugging

    threading.Thread(target=ping_storages).start()

    while True:
        # print('naming server listening for client')

        con, address = sock.accept()
        clients.append(con)
        name = 'da_client'
        # print(name + ' connected from ' + str(address[0]))
        clientListener = ClientListener(name, con, address[0])
        clientListener.start()
