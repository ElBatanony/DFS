import socket
import shutil
from pathlib import Path
import os

from constants_and_codes import *
from helpers import *

path = CLIENT_ROOT_PATH

def get_prev(path): return '/'.join(path.split('/')[:-1])
def get_last(path): return path.split('/')[-1]
def storage_path(): return '/'.join(path.split('/')[1:])
def storage_path_plus():
    ret = storage_path()
    if ret != '': ret += '/'
    return ret
def path_plus(): return path + '/'

def initialize(sock):
    send_code(sock, CMD_INIT)
    ret = receive_code(sock)

    if ret != CODE_OK:
        print("Error with initalizing on server. Error: " + str(ret) )
        return

    try: # Delete local dfs and all its content
        shutil.rmtree(CLIENT_ROOT_PATH)
    except OSError as e:
        print("Error deleting client files directory: %s - %s." % (e.filename, e.strerror))
        return

    try:  # Recreate the local dfs directory
        os.mkdir(CLIENT_ROOT_PATH)
    except OSError as e:
        print("Error creating client files directory: %s - %s." % (e.filename, e.strerror))
        return

    global path # reset root path to client root path
    path = CLIENT_ROOT_PATH

    print('Initalization complete. You have ' + str(INITIAL_SIZE) + ' MBs available.')

def create_file(sock, file_name):
    file_path = path_plus() + file_name
    if os.path.isfile(file_path):
        print('File to create already exists on local machine')
        return
    
    with open(file_path, "wb") as myfile:
        myfile.write(b"Empty file")
        myfile.close()
    
    if not write_file(sock, file_name):
        print("Could not write empty file to storage server")
        os.remove(file_path)
        return
    print('Created empty file.')

def read_file(sock, file_name):

    send_code(sock, CMD_READ_FILE)
    file_path = storage_path_plus() + file_name
    send_str(sock, file_path)
    ret = receive_code(sock)
    if ret != CODE_OK:
        print('Error reading file from naming server! Error: ' + str(ret) )
        return

    file_id = receive_str(sock)
    storage_servers = receive_str(sock).split(',')

    for storage_server_ip in storage_servers:
        storage_sock = open_socket(storage_server_ip, STORAGE_SERVER_PORT)
        if not storage_sock:
            continue
        send_code(storage_sock, CMD_READ_FILE)
        send_str(storage_sock, file_id)
        ret = receive_code(storage_sock)
        if ret != CODE_OK:
            print('Error reading file from storage server. Error code: ' + str(ret) )
            continue
        file_path = path_plus() + file_name
        receive_file(storage_sock, file_path)
        print('File read completed.')
        return
    
    print('File  was not read successfully!')
    
def write_file(sock, file_name):

    file_path_local = path_plus() + file_name

    if not os.path.isfile( file_path_local ):
        print('File to write does not exist!')
        return False

    send_code(sock, CMD_WRITE_FILE)
    send_str(sock, storage_path_plus() + file_name)
    send_int32(sock, os.path.getsize(file_path_local))

    ret = receive_code(sock)
    if ret != CODE_OK:
        print('Error writing file (Part 1) from naming server. Error code: ' + str(ret) )
        return False

    file_id = receive_str(sock)
    storage_servers = receive_str(sock).split(',')

    if len(storage_servers) == 0:
        print('No storage servers found to write file to')
        return False

    for storage_server_ip in storage_servers:
        storage_sock = open_socket( storage_server_ip , STORAGE_SERVER_PORT )
        send_code(storage_sock, CMD_WRITE_FILE)
        send_str(storage_sock, file_id)
        #print('Sending file ' + file_path_local + ' to ' + stora)
        send_file(storage_sock, file_path_local)
        confirmation = receive_code(storage_sock)
        if confirmation != CODE_OK:
            print('File not received by storage server.')
            continue
        
        print('File received by storage server.')
        break

    print('File write completed!')
    return True

def delete_file(sock, file_name):

    if not os.path.isfile(path_plus() + file_name):
        print('File does not exist on machine. Maybe try "ls".')
        return
    
    send_code(sock, CMD_DELETE_FILE)
    send_str(sock, storage_path_plus() + file_name )
    ret = receive_code(sock)
    if ret != CODE_OK:
        print('Error deleting file. Error code: ' + str(ret) )
        return
    os.remove( path_plus() + file_name)
    print('File deleted successfully')

def file_info(sock, file_name):
    send_code(sock, CMD_FILE_INFO)
    send_str(sock, storage_path_plus() + file_name)
    ret = receive_code(sock)
    if ret != CODE_OK:
        print('Error getting file info. Error code: ' + str(ret) )
        return
    finfo = receive_str(sock)
    print('File information: ' + finfo)

def copy_file(sock, old_file_name, new_file_name):
    send_code(sock, CMD_COPY_FILE)
    send_str(sock, storage_path_plus() + old_file_name)
    send_str(sock, storage_path_plus() + new_file_name)
    ret = receive_code(sock)
    if ret != CODE_OK:
        print('Error copying file. Error code: ' + str(ret) )
        return
    shutil.copy( path_plus() + old_file_name, path_plus() + new_file_name )

def move_file(sock, file_name, new_dir):

    if not os.path.isdir(path_plus() + file_name):
        print('The directory you trying to move file to does not exist. Maybe try "ls" at that location.')
        return

    send_code(sock, CMD_FILE_MOVE)
    send_str(sock, storage_path_plus() + file_name )
    ret = receive_code(sock)
    if ret != CODE_OK:
        print('Error moving file (Part 1). Error code: ' + str(ret) )
        return
    
    if new_dir == 'root': new_dir = ''
    send_str(sock, new_dir)
    ret = receive_code(sock)
    if ret != CODE_OK:
        print('Error moving file (Part 2). Error code: ' + str(ret) )
        return
    
    new_path = CLIENT_ROOT_PATH + '/' + new_dir + '/' + file_name
    if new_dir == '': new_path = CLIENT_ROOT_PATH + '/' + file_name
    
    try:
        shutil.move(path_plus() + file_name, new_path)
    except OSError as e:
        print("Error moving file (Part 3): %s - %s." % (e.filename, e.strerror))
        return
    
    print('File moved successfully.')


def open_directory(sock, directory_name):
    global path

    if directory_name == '..':
        if path == CLIENT_ROOT_PATH:
            print('You are already in root directory. Current path: ' + path)
            return
        path = get_prev(path)
        print('Entered previous directory. Current path: ' + path)
        return

    send_code(sock, CMD_CHECK_DIR)
    send_str(sock, storage_path_plus() + directory_name)
    ret = receive_code(sock)

    if ret != CODE_OK:
        print('Directory does not exist (on naming server). Error code: ' + str(ret) )
        return

    path = path_plus() + directory_name

    if not os.path.isdir(path):
        print('Directory did not exist in local files. Created it. Try using "ls" before entering next time.')
        os.mkdir(path)

    print('Entered directory successfully.')

def read_directory(sock):
    send_code(sock, CMD_READ_DIR)
    send_str(sock, storage_path())

    ret = receive_code(sock)
    if ret != CODE_OK:
        print('Error reading directory. Error code: ' + str(ret) )
        return

    dir = receive_str(sock)

    # create empty directories according to ls
    for x in dir.split(','):
        if len(x) > 0 and x[-1] == '/':
            new_dir_name = x[:-1]
            if not os.path.exists(path_plus() + new_dir_name):
                print('Created directory ' + new_dir_name)
                os.mkdir(path_plus() + new_dir_name)
    
    print(path+': ' + dir.replace(',', ' ') )

def make_directory(sock, directory_name):
    send_code(sock, CMD_MAKE_DIR)
    send_str(sock, storage_path_plus() + directory_name )
    ret = receive_code(sock)
    if ret != CODE_OK:
        print('Error creating a new directory. Error code: ' + str(ret) )
        return

    if not os.path.isdir(path_plus() + directory_name):
        os.mkdir(path_plus() + directory_name)
    else:
        print('Directory already existed on local machine.')
    
    print('Directory created succssfully')

def delete_directory(sock, directory_name, force):

    if not os.path.isdir(path_plus() + directory_name):
        print('This directory does not exist on your machine. Maybe try "ls" first.')
        return

    send_code(sock, CMD_DELETE_DIR)
    send_str(sock, storage_path_plus() + directory_name)
    send_str(sock, str(force) )
    ret = receive_code(sock)

    if ret != CODE_OK:
        print('Error deleting directory from servers.')
        return

    try:
        shutil.rmtree(path_plus() + directory_name)
    except OSError as e:
        print("Error deleting directory: %s - %s." % (e.filename, e.strerror))
    
    print('Directory deleted successfuly')

if __name__ == "__main__":

    if not os.path.isdir(CLIENT_ROOT_PATH):
        os.mkdir(CLIENT_ROOT_PATH)

    cmd = ''
    while True:
        
        naming_server_sock = open_socket(NAMING_SERVER_IP, int(NAMING_SERVER_PORT))

        if not naming_server_sock:
            break

        inp = input('Enter command: ')
        cmd = inp.split(' ')[0]
        args = inp.split(' ')[1:] # double check that arguments are not empty strings

        if cmd == 'init' and len(args) == 0: initialize(naming_server_sock)
        elif cmd == 'touch' and len(args) == 1: create_file(naming_server_sock, args[0])
        elif cmd == 'r' and len(args) == 1: read_file(naming_server_sock, args[0])
        elif cmd == 'w' and len(args) == 1: write_file(naming_server_sock, args[0])
        elif cmd == 'rm' and len(args) == 1: delete_file(naming_server_sock, args[0])
        elif cmd == 'info' and len(args) == 1: file_info(naming_server_sock, args[0])
        elif cmd == 'cp' and len(args) == 2: copy_file(naming_server_sock, args[0], args[1])
        elif cmd == 'mv' and len(args) == 2: move_file(naming_server_sock, args[0], args[1])
        elif cmd == 'cd' and len(args) == 1: open_directory(naming_server_sock, args[0])
        elif cmd == 'ls' and len(args) == 0: read_directory(naming_server_sock)
        elif cmd == 'mkdir' and len(args) == 1: make_directory(naming_server_sock, args[0])
        elif cmd == 'rmdir' and len(args) == 1: delete_directory(naming_server_sock, args[0], False)
        elif cmd == 'rmdir' and len(args) == 2: delete_directory(naming_server_sock, args[0], True)
        elif cmd == 'exit': pass
        else: print('Command-arguments combination unrecognized')
        
        naming_server_sock.close()
        if cmd == 'exit':
            print('Exiting')
            break
