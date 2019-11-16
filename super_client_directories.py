import os
import shutil
from constants import *
from status_codes import *
from sender import *
from receiver import *

path = CLIENT_ROOT_PATH

def reset_path():
    global path
    path = CLIENT_ROOT_PATH

def get_prev(path): return '/'.join(path.split('/')[:-1])

def get_last(path): return path.split('/')[-1]

def storage_path():
    return '/'.join(path.split('/')[1:])

def storage_path_plus():
    sp = storage_path()
    if sp != '':
        return sp + '/'
    return sp

def path_plus():
    if path != '':
        return path + '/'
    return path

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
