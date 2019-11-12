import os
import socket
from threading import Thread
from status_codes import *

clients = []

directories = {}

class Directory:
    def __init__(self, path):
        self.path = path
        self.directories = []
        self.files = []

    def __str__(self):
        return 'path:' + self.path + ', dirs:' + str(self.directories) + ', files:' + str(self.files)

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
        directories[ get_prev(directory_path) ].directories.remove( directory_name )
        del directories[ directory_path ]

        return DIR_DELETE_OK
    else:
        return DIR_DELETE_NOT_EXIST

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
        return directories[self.path]
    
    def make_directory(self, directory_name):
        return make_directory_by_path( self.path + '/' + directory_name )

    def delete_directory(self, directory_name, force=False):
        return delete_directory_by_path( self.path + '/' + directory_name, force )
    
    def run(self):
        file_name_size = int.from_bytes(
            bytes=self.sock.recv(32), byteorder='big', signed=False)

        if file_name_size is None:
            self._close()
            print('Error during file name size reading.')
            return

        file_size = int.from_bytes(bytes=self.sock.recv(
            64), byteorder='big', signed=False)

        if file_size is None:
            self._close()
            print('Error during file size reading.')
            return

        file_name = self.sock.recv(file_name_size).decode('UTF-8')
        file_name = ClientListener._get_file_name(file_name)

        with open(file_name, 'wb') as sw:

            received_size = 0

            while received_size < file_size:
                buffer = min(file_size - received_size, 1024)
                file = self.sock.recv(buffer)
                received_size += buffer
                if file is None:
                    self._close()
                    print('Error during file transfer.')
                    return
                sw.write(file)

            print(file_name + ' received.')

def test_client() :
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tc = ClientListener('testing_client', sock)
    print(tc.make_directory('hi'))
    print(tc.open_directory('hi'))
    print(tc.open_directory('..')) 
    print(tc.open_directory('..'))
    print(tc.read_directory() )
    print(tc.delete_directory('hi'))

if __name__ == "__main__":
    test_client()
