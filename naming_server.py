import socket
import sys
import uuid
import threading
import time
from threading import Thread

from status_codes import *
from helpers import *
from constants import *

directories = {}
storage_servers = []
write_file_map = {}

def get_prev(path): return '/'.join(path.split('/')[:-1])
def get_last(path): return path.split('/')[-1]
def get_storages(): return ','.join(storage_servers)

class File:
    def __init__(self, name: str, size: int):
        self.name = name
        self.size = size
        self.id = str(uuid.uuid4())

class Directory:
    def __init__(self, path):
        self.path = path
        self.directories = []
        self.files = {}


def ping_storages():
    while True:
        print('Pining storage servers. ' + get_storages() )
        for storage_server_ip in storage_servers:
            storage_sock = open_socket(storage_server_ip, STORAGE_SERVER_PORT)
            if not storage_sock:
                storage_servers.remove(storage_server_ip)
            
            send_code(storage_sock, CMD_PING_FROM_NAMING)
            ret = receive_code(storage_sock)
            if ret != CODE_OK:
                storage_servers.remove(storage_server_ip)
                print('Lost storage server: ' + storage_server_ip)
        time.sleep(PING_SERVERS_SECONDS)

def ping_from_storage(sock, ip):
    storage_servers.append(ip)
    print('Storage server ' + ip + ' connected.')
    send_code(sock, CODE_OK)

    if len( storage_servers ) > 0:
        for dir in directories.values():
            for f in dir.files.values():
                storage_sock = open_socket(ip, STORAGE_SERVER_PORT)
                send_code(storage_sock, CMD_REPLICATE_FILE)
                send_str(storage_sock, storage_servers[0])
                send_str(storage_sock, f.id)                

def confirm_file_upload(sock, ip):
    file_id = receive_str(sock)

    if file_id not in write_file_map:
        print('Storage confirming unided file.')
        return
    
    f, file_dir_path = write_file_map[file_id]
    directories[file_dir_path].files[f.name] = f
    del write_file_map[file_id]
    print('File ' + f.name + ' upload confirmed.')

    for storage_server_ip in storage_servers:
        if storage_server_ip == ip:
            continue
        storage_sock = open_socket(storage_server_ip, STORAGE_SERVER_PORT)
        if not storage_sock:
            continue
        send_code(storage_sock, CMD_REPLICATE_FILE)
        send_str(storage_sock,  ip)
        send_str(storage_sock, f.id)
        ret = receive_code(storage_sock)
        if ret != CODE_OK:
            print('Error replicating file on storage server ' + storage_server_ip)
    
def initialize(sock):
    global directories

    for storage_server_ip in storage_servers:
        storage_sock = open_socket(storage_server_ip, STORAGE_SERVER_PORT)
        if not storage_servers:
            continue
        send_code(storage_sock, CMD_INIT)

    directories = {}
    directories[''] = Directory('')
    send_code(sock, CODE_OK)

def read_file(sock):
    file_path = receive_str(sock)
    file_dir_path = get_prev(file_path)
    file_name = get_last(file_path)

    if file_dir_path not in directories:
        send_code(sock, ERR_DIR_NOT_EXIST)
        return

    file_dir = directories[file_dir_path]
    if file_name not in file_dir.files:
        send_code(sock, ERR_FILE_NOT_EXIST)
        return

    send_code(sock, CODE_OK)
    f = file_dir.files[file_name]
    send_str(sock, f.id)
    send_str(sock, get_storages() )


def write_file(sock):
    file_path = receive_str(sock)
    file_size = receive_int64(sock)

    file_dir_path = get_prev(file_path)

    if file_dir_path not in directories:
        send_code(sock, ERR_DIR_NOT_EXIST)
        return

    file_name = get_last(file_path)
    file_dir = directories[file_dir_path]

    if file_name in file_dir.files:
        send_code(sock, ERR_FILE_EXISTS)
        return
    
    new_file = File(file_name, file_size)
    write_file_map[new_file.id] = new_file, file_dir_path

    send_code(sock, CODE_OK)
    send_str(sock, new_file.id)
    send_str(sock, get_storages() )

def delete_file(sock):
    file_path = receive_str(sock)

    file_dir_path = get_prev(file_path)

    if file_dir_path not in directories:
        send_code(sock, ERR_DIR_NOT_EXIST)
        return
    
    file_dir = directories[file_dir_path]
    file_name = get_last(file_path)

    if file_name not in file_dir.files:
        send_code(sock, ERR_FILE_NOT_EXIST)
        return
    
    f = file_dir.files[file_name] 

    for storage_server_ip in storage_servers:
        storage_sock = open_socket(storage_server_ip, STORAGE_SERVER_PORT)
        if not storage_sock:
            continue
        send_code(storage_sock, CMD_DELETE_FILE)
        send_str(storage_sock, f.id)
        ret = receive_code(storage_sock)
        if ret != CODE_OK:
            print('Error deleting file on ' + storage_server_ip)

    del file_dir.files[file_name]

    send_code(sock, CODE_OK)

def file_info(sock):
    file_path = receive_str(sock)
    file_dir_path = get_prev(file_path)
    file_name = get_last(file_path)
    
    if file_dir_path not in directories:
        send_code(sock, ERR_DIR_NOT_EXIST)
        return
    
    file_dir = directories[file_dir_path]

    if file_name not in file_dir.files:
        send_code(sock, ERR_FILE_NOT_EXIST)
        return
    
    send_code(sock, CODE_OK)

    f = file_dir.files[file_name]
    ret = 'name: {}, size{} bytes, id: {}'.format(f.name, str(f.size), f.id)
    send_str(sock, ret)


def copy_file(sock):

    old_file_path = receive_str(sock)
    new_file_path = receive_str(sock)

    old_file_dir_path = get_prev(old_file_path)
    new_file_dir_path = get_prev(new_file_path)

    if old_file_dir_path not in directories or new_file_dir_path not in directories:
        send_code(sock, ERR_DIR_NOT_EXIST)
        return
    
    old_file_dir = directories[old_file_dir_path]
    new_file_dir = directories[new_file_dir_path]
    
    old_file_name = get_last(old_file_path)
    new_file_name = get_last(new_file_path)

    if old_file_name not in old_file_dir.files:
        send_code(sock, ERR_FILE_NOT_EXIST)
        return

    old_file = old_file_dir.files[old_file_name]

    if new_file_name in new_file_dir.files:
        send_code(sock, ERR_FILE_EXISTS)
        return
    
    new_file = File(new_file_name, old_file.size)
    new_file_dir.files[new_file_name] = new_file

    for storage_server_ip in storage_servers:
        storage_sock = open_socket(storage_server_ip, STORAGE_SERVER_PORT)
        if not storage_sock:
            continue
        
        send_code(storage_sock, CMD_COPY_FILE)
        send_str(storage_sock, old_file.id)
        send_str(storage_sock, new_file.id)

        ret = receive_code(storage_sock)
        if ret != CODE_OK:
            print('Error copying file to ' + storage_server_ip +". Error code: " + str(ret) )

    send_code(sock, CODE_OK)

def move_file(sock):

    global directories

    old_file_path = receive_str(sock)
    
    old_file_dir_path = get_prev(old_file_path)
    old_file_name = get_last(old_file_path)

    if old_file_dir_path not in directories:
        send_code(sock, ERR_DIR_NOT_EXIST)
        return
    
    old_file_dir = directories[old_file_dir_path]

    if old_file_name not in old_file_dir.files:
        send_code(sock, ERR_FILE_NOT_EXIST)
        return

    send_code(sock, CODE_OK)
    
    new_file_dir_path = receive_str(sock)

    if new_file_dir_path not in directories:
        send_code(sock, ERR_DIR_NOT_EXIST)
        return
    
    new_file_dir = directories[new_file_dir_path]

    if old_file_name in new_file_dir.files:
        send_code(sock, ERR_FILE_EXISTS)
        return

    old_file = old_file_dir.files[old_file_name]
    new_file = File(old_file.name, old_file.size)
    new_file.id = old_file.id
    directories[new_file_dir_path].files[old_file_name] = new_file
    del directories[old_file_dir_path].files[old_file_name]
    
    send_code(sock, CODE_OK)

def check_directory(sock):
    dir_path = receive_str(sock)

    print('checking directory ' + dir_path)

    if dir_path not in directories:
        send_code(sock, ERR_DIR_NOT_EXIST)
        return
    send_code(sock, CODE_OK)

def read_directory(sock):
    # check directories and files with spaces
    dir_path = receive_str(sock)

    print('reading directory ' + dir_path)

    if dir_path not in directories:
        send_code(sock, ERR_DIR_NOT_EXIST)
        return
    
    send_code(sock, CODE_OK)

    ret = ''
    for directory in directories[dir_path].directories:
        ret += directory + '/,'
    for f in directories[dir_path].files.keys():
        ret += f + ','
    ret = ret[:-1]
    send_str(sock, ret)

def make_directory(sock):

    global directories
    dir_path = receive_str(sock)
    
    print('creating directory ' + dir_path)

    if dir_path in directories:
        send_code(sock, ERR_DIR_EXISTS)
        return
    

    directories[dir_path] = Directory(dir_path)
    directory_name = get_last(dir_path)
    directories[get_prev(dir_path)].directories.append(directory_name)
    send_code(sock, CODE_OK)

def delete_dir_by_path(dir_path, force):

    print('deleting directory ' + dir_path + ', ' + str(force) )

    if dir_path not in directories:
        return ERR_DIR_NOT_EXIST

    dir = directories[dir_path]

    if len(dir.files) > 0 or len(dir.directories) > 0:
        if not force:
            return DIR_DELETE_HAS_FILES

    for f in dir.files:
        for storage_server_ip in storage_servers:
            storage_sock = open_socket(storage_server_ip, STORAGE_SERVER_PORT)
            if not storage_sock:
                continue
            send_code(storage_sock, CMD_DELETE_FILE)
            send_str(storage_sock, f.id)
            ret = receive_code(storage_sock)
            if ret != CODE_OK:
                print('Error deleting file on storage server ' + storage_server_ip)

    for directory in dir.directories:
        delete_dir_by_path( dir_path + '/' if dir_path != '' else '' + directory, True )

    dir_name = get_last(dir_path)
    dir_parent = get_prev(dir_path)

    directories[dir_parent].directories.remove(dir_name)
    del directories[dir_path]
    return CODE_OK

def delete_directory(sock):
    dir_path = receive_str(sock)
    force = bool(receive_str(sock))
    ret = delete_dir_by_path(dir_path, force)
    send_code(sock, ret)
    
class ClientListener(Thread):

    def __init__(self, name: str, sock: socket.socket):
        super().__init__(daemon=True)
        self.sock = sock
        self.name = name
        self.path = name

    def _close(self):
        self.sock.close()
        # logger.info(self.name + ' disconnected')

    def run(self):
        try:
            cmd = receive_code(self.sock)
        except Exception as e:
            print('Error receving command from connection. Error:' + str(e))
            self._close()
            return

        print("Received " + str(cmd) + " from " + self.name)

        if cmd == CMD_PING_FROM_STORAGE: ping_from_storage(self.sock, self.name)
        elif cmd == CMD_CONFIRM_FILE_UPLOAD: confirm_file_upload(self.sock, self.name)
        elif cmd == CMD_INIT: initialize(self.sock)
        elif cmd == CMD_READ_FILE: read_file(self.sock)
        elif cmd == CMD_WRITE_FILE: write_file(self.sock)
        elif cmd == CMD_DELETE_FILE: delete_file(self.sock)
        elif cmd == CMD_FILE_INFO: file_info(self.sock)
        elif cmd == CMD_COPY_FILE: copy_file(self.sock)
        elif cmd == CMD_FILE_MOVE: move_file(self.sock)
        elif cmd == CMD_CHECK_DIR: check_directory(self.sock)
        elif cmd == CMD_READ_DIR: read_directory(self.sock)
        elif cmd == CMD_MAKE_DIR: make_directory(self.sock)
        elif cmd == CMD_DELETE_DIR: delete_directory(self.sock)
        else: print('Received unknown command. Command: ' + str(cmd) )

        self._close()

if __name__ == "__main__":
    directories[''] = Directory('')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', NAMING_SERVER_PORT))
    sock.listen()

    #sock.settimeout(10)  # for testing

    threading.Thread(target=ping_storages).start()

    while True:
        print('Naming server listening...')
        con, address = sock.accept()
        conip = str(address[0])
        print( conip + ' connected.')
        clientListener = ClientListener(conip, con)
        clientListener.start()
