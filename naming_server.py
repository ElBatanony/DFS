import os
import socket
from threading import Thread
from status_codes import *
from web_format_converter import int64_to_web, web_to_int, int32_to_web
from receiver import receive_str, receive_file
from sender import send_file, send_str
from constants import *
import time

clients = []

directories = {}

class Directory:
    def __init__(self, path):
        self.path = path
        self.directories = []
        self.files = {}

class File:
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.id = 'random'
        self.storage = ['ip1', 'ip2', 'ip3']

def get_prev(path):
    return '/'.join(path.split('/')[:-1])

def get_last(path):
    return path.split('/')[-1]

def delete_file_by_path(file_path):
    return

''' Directory Functions '''

def make_directory_by_path(directory_path):
    if directory_path in directories:
        return DIR_MAKE_EXISTS
    directories[ directory_path ] = Directory(directory_path)
    directory_name = get_last(directory_path)
    directories[ get_prev(directory_path) ].directories.append( directory_name )
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
        if get_prev(directory_path) != '' : directories[get_prev(directory_path)].directories.remove(directory_name)
        del directories[ directory_path ]

        return DIR_DELETE_OK
    else:
        return DIR_DELETE_NOT_EXIST

def file_info_by_path(file_path):
    file_dir = get_prev(file_path)
    file_name = get_last(file_path)
    if file_dir in directories:
        if file_name in directories[file_dir].files:
            f = directories[file_dir].files[file_name]
            ret = '{},{},{},{},{},{}'.format( f.name, f.id, str(f.size), f.storage[0], f.storage[1], f.storage[2] )
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
        directories[name] = Directory(name)

    def _close(self):
        clients.remove(self.sock)
        self.sock.close()
        print(self.name + ' disconnected')

    ''' Files Section '''
    def delete_file(self, file_name):
        return delete_file_by_path(self.path + '/' + file_name)
    
    ''' Directories Section '''
    def open_directory(self, directory_name):
        if directory_name == '..':
            if self.name == self.path:
                return DIR_OPEN_ROOT
            self.path = get_prev( self.path )
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
        return make_directory_by_path( self.path + '/' + directory_name )

    def delete_directory(self, directory_name, force=False):
        return delete_directory_by_path( self.path + '/' + directory_name, force )

    def file_info(self, file_name):
        return file_info_by_path( self.path + '/' + file_name )
    
    def move_file(self, file_name, new_path):
        return move_file_by_path(self.path + '/' + file_name, new_path)
    
    def run(self):
        cmd = ''
        while True:
            cmd = web_to_int(self.sock.recv(32))

            if cmd == CODE_WRITE_FILE:
                self.write_file()
            elif cmd == CODE_READ_FILE:
                self.read_file()
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
                send_str(self.sock, 'Storage initialized. You have '+ str(INITIAL_SIZE) + ' MBs available.')
            elif cmd == CMD_FILE_INFO:
                file_name = receive_str(self.sock)
                ret = self.file_info(file_name)
                send_str(self.sock, ret)
            elif cmd == CMD_FILE_MOVE:
                file_name = receive_str(self.sock)
                new_path = receive_str(self.sock)
                ret = self.move_file(file_name, new_path)
                send_str(self.sock, ret)

            elif cmd == CMD_CLOSE_SOCK:
                break
            else:
                print('Error reading command code.')

        self.sock.close()

if __name__ == "__main__":

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 8800))
    sock.listen()

    print('Naming server listening for client')
    
    con, addr = sock.accept()
    clients.append(con)
    name = 'da_client'
    print( name + ' connected from ' + str(addr[0]) )
    clientListener = ClientListener(name, con)
    clientListener.start()

    # only for testing, this kills server after client disconnects
    while clientListener.isAlive():
        time.sleep(0.5)
    
    print('Naming server shutting down. Probably should save.')

