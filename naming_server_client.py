import os
import socket

from constants import CLIENT_ROOT_PATH, NAMING_SERVER_IP, NAMING_SERVER_PORT
from logs import logger
from receiver import receive_int32, receive_str
from sender import send_int32, send_str, send_int64
from status_codes import CMD_DELETE_FILE, CODE_OK, CMD_PING_AS_STORAGE, CMD_CONFIRM_FILE_UPLOAD, CMD_GET_STORAGE, \
    CMD_WRITE_FILE, CMD_READ_FILE, CMD_COPY_FILE, CMD_OPEN_DIR, CMD_READ_DIR, CMD_MAKE_DIR, CMD_DELETE_DIR, CMD_INIT, \
    CMD_FILE_INFO, CMD_FILE_MOVE


def delete_file(sock: socket.socket, file_name: str):
    send_int32(sock, CMD_DELETE_FILE)
    send_str(sock, file_name)
    try:
        code = receive_int32(sock)
    except Exception as e:
        logger.info(str(e))
        return False
    if code != CODE_OK:
        logger.info('error with code %d when deleting file' % code)
        return False
    file_path = os.path.join(CLIENT_ROOT_PATH, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    return True


def ping_as_storage(sock: socket.socket):
    send_int32(sock, CMD_PING_AS_STORAGE)
    try:
        port = receive_int32(sock)
    except Exception as e:
        logger.info(str(e))
        return None
    logger.info('allocated storage server port: %d' % port)
    return port


def confirm_file_upload(sock: socket.socket, port: int, file_id: str):
    send_int32(sock, CMD_CONFIRM_FILE_UPLOAD)
    send_int32(sock, port)
    send_str(sock, file_id)
    try:
        code = receive_int32(sock)
    except Exception as e:
        logger.info(str(e))
        return False
    if code != CODE_OK:
        return False
    return True


def get_storage(sock: socket.socket):
    send_int32(sock, CMD_GET_STORAGE)
    size = receive_int32(sock)
    storage = []
    for i in range(size):
        try:
            storage.append(receive_int32(sock))
        except Exception as e:
            logger.info(str(e))
            return False

    logger.info('received storage: %s' % str(storage))
    return storage


def write_file(sock: socket.socket, file_name: str):
    if not os.path.exists(os.path.join(CLIENT_ROOT_PATH, file_name)):
        logger.info('error "file does not exist" received')
        return False

    send_int32(sock, CMD_WRITE_FILE)
    send_str(sock, file_name)
    send_int64(sock, os.path.getsize(os.path.join(CLIENT_ROOT_PATH, file_name)))

    try:
        code = receive_int32(sock)
    except Exception as e:
        logger.info(str(e))
        return False

    if code != CODE_OK:
        logger.info('error with code %d received after sending "write_file" from naming server client' % code)
        return False

    try:
        file_id = receive_str(sock)
    except Exception as e:
        logger.info(str(e))
        return False

    logger.info('received file id %s' % file_id)
    return file_id


def read_file(sock: socket.socket, file_name: str):
    send_int32(sock, CMD_READ_FILE)
    send_str(sock, file_name)

    try:
        code = receive_int32(sock)
    except Exception as e:
        logger.info(str(e))
        return False

    if code != CODE_OK:
        logger.info('error with code %d' % code)
        return False

    try:
        file_id = receive_str(sock)
    except Exception as e:
        logger.info(str(e))
        return False

    logger.info('received file id %s' % file_id)
    return file_id


def copy_file(sock: socket.socket, source_file_name: str, destination_file_name: str):
    send_int32(sock, CMD_COPY_FILE)
    send_str(sock, source_file_name)
    send_str(sock, destination_file_name)
    try:
        code = receive_int32(sock)
    except Exception as e:
        logger.info(str(e))
        return False
    if code != CODE_OK:
        logger.info('error with code %d' % code)
        return False
    logger.info('file copied')
    return True


def open_directory(sock: socket.socket, directory_name: str):
    send_int32(sock, CMD_OPEN_DIR)
    send_str(sock, directory_name)
    ret = receive_str(sock)
    logger.info('cd response: ' + ret)


def read_directory(sock: socket.socket):
    send_int32(sock, CMD_READ_DIR)
    d = receive_str(sock)
    logger.info('ls response: ' + d)


def make_directory(sock: socket.socket, directory_name: str):
    send_int32(sock, CMD_MAKE_DIR)
    send_str(sock, directory_name)
    ret = receive_str(sock)
    logger.info('mkdir response: ' + ret)


def delete_directory(sock: socket.socket, directory_name: str):
    send_int32(sock, CMD_DELETE_DIR)
    send_str(sock, directory_name)
    ret = receive_str(sock)
    logger.info('rmdir response: ' + ret)


def init_server(sock: socket.socket):
    send_int32(sock, CMD_INIT)
    ret = receive_str(sock)
    logger.info('init response: ' + ret)


def file_info(sock: socket.socket, file_name: str):
    send_int32(sock, CMD_FILE_INFO)
    send_str(sock, file_name)
    ret = receive_str(sock)
    logger.info('info response: ' + ret)


def move_file(sock: socket.socket, file_name: str, new_path: str):
    send_int32(sock, CMD_FILE_MOVE)
    send_str(sock, file_name)
    send_str(sock, new_path)
    ret = receive_str(sock)
    logger.info('mv response: ' + ret)


def send_command_to_naming_server(cmd: int, args: list):
    host = NAMING_SERVER_IP

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, NAMING_SERVER_PORT))

    logger.info('send command %d to naming server' % cmd)

    result = None
    if cmd == CMD_CONFIRM_FILE_UPLOAD and len(args) == 2:
        result = confirm_file_upload(sock, args[0], args[1])
    elif cmd == CMD_GET_STORAGE and len(args) == 0:
        result = get_storage(sock)
    elif cmd == CMD_WRITE_FILE and len(args) == 1:
        result = write_file(sock, args[0])
    elif cmd == CMD_READ_FILE and len(args) == 1:
        result = read_file(sock, args[0])
    elif cmd == CMD_COPY_FILE and len(args) == 2:
        result = copy_file(sock, args[0], args[1])
    elif cmd == CMD_DELETE_FILE and len(args) == 1:
        result = delete_file(sock, args[0])
    elif cmd == CMD_OPEN_DIR and len(args) == 1:
        open_directory(sock, args[0])
    elif cmd == CMD_READ_DIR and len(args) == 0:
        read_directory(sock)
    elif cmd == CMD_MAKE_DIR and len(args) == 1:
        make_directory(sock, args[0])
    elif cmd == CMD_DELETE_DIR and len(args) == 1:
        delete_directory(sock, args[0])
    elif cmd == CMD_INIT and len(args) == 0:
        init_server(sock)
    elif cmd == CMD_FILE_INFO and len(args) == 1:
        file_info(sock, args[0])
    elif cmd == CMD_FILE_MOVE and len(args) == 2:
        move_file(sock, args[0], args[1])
    elif cmd == CMD_PING_AS_STORAGE and len(args) == 0:
        result = ping_as_storage(sock)
    else:
        logger.info('error reading command %d with args %s' % (cmd, str(args)))

    sock.close()
    return result
