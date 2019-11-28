import os
import socket

from constants import CLIENT_ROOT_PATH, NAMING_SERVER_IP
from logs import logger
from receiver import receive_int32, receive_str, receive_file
from sender import send_int32, send_str, send_file
from status_codes import CMD_PING_AS_NAMING, CODE_OK, CMD_REPLICATE_FILE, CMD_FILE_INFO, CMD_DELETE_FILE, \
    CMD_COPY_FILE, CMD_READ_FILE, CMD_WRITE_FILE


def ping_as_naming(sock):
    send_int32(sock, CMD_PING_AS_NAMING)
    ret = receive_int32(sock)
    if ret != CODE_OK:
        return False
    return True


def replicate_file(sock: socket.socket, port: int, file_name: str):
    send_int32(sock, CMD_REPLICATE_FILE)
    send_int32(sock, port)
    send_str(sock, file_name)
    code = receive_int32(sock)
    if code != CODE_OK:
        logger.info('error with code %d' % code)
        return False
    return True


def get_file_info(sock: socket.socket, file_name):
    send_int32(sock, CMD_FILE_INFO)
    send_str(sock, file_name)
    code = receive_int32(sock)
    if code != CODE_OK:
        logger.info('error with code %d' % code)
        return False
    file_info = receive_str(sock)
    logger.info(file_info)
    return True


def delete_file(sock, file_name):
    send_int32(sock, CMD_DELETE_FILE)
    send_str(sock, file_name)
    code = receive_int32(sock)
    if code != CODE_OK:
        logger.info('error with code %d' % code)
        return False
    logger.info('file removed')
    return True


def copy_file(sock, old_file_name, new_file_name):
    send_int32(sock, CMD_COPY_FILE)
    send_str(sock, old_file_name)
    send_str(sock, new_file_name)
    code = receive_int32(sock)
    if code != CODE_OK:
        logger.info('error with code %d' % code)
        return False
    logger.info('file copied')
    return True


def read_file(sock: socket.socket, path_to_source_file: str, path_to_destination_file: str, root_dir: str):
    send_int32(sock, CMD_READ_FILE)
    send_str(sock, path_to_source_file)
    code = receive_int32(sock)
    if code != CODE_OK:
        logger.info('error with code %d' % code)
        return False
    try:
        receive_file(sock, path_to_destination_file, root_dir)
    except Exception as e:
        logger.info(str(e))
        return False
    return True


def write_file(sock, path_to_source_file: str, path_to_destination_file: str, root_dir: str):
    if not os.path.exists(os.path.join(CLIENT_ROOT_PATH, path_to_source_file)):
        raise Exception('file does not exist')

    send_int32(sock, CMD_WRITE_FILE)
    send_str(sock, path_to_destination_file)
    send_file(sock, path_to_source_file, root_dir)
    try:
        code = receive_int32(sock)
    except Exception as e:
        logger.info(str(e))
        return False
    if code != CODE_OK:
        logger.info('error with code %d' % str(code))
        return False
    return True


def send_command_to_storage_server(port: int, cmd: int, args):
    if args is None:
        args = []

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.connect((NAMING_SERVER_IP, port))
    except Exception as e:
        logger.info(str(e))
        return False

    logger.info('send command %d to storage server on port %d' % (cmd, port))

    result = None

    if cmd == CMD_WRITE_FILE and len(args) == 3:
        result = write_file(sock, args[0], args[1], args[2])
    elif cmd == CMD_READ_FILE and len(args) >= 2:
        if len(args) == 3:
            result = read_file(sock, args[0], args[1], args[2])
        else:
            result = read_file(sock, args[0], args[1], CLIENT_ROOT_PATH)
    elif cmd == CMD_COPY_FILE and len(args) == 2:
        result = copy_file(sock, args[0], args[1])
    elif cmd == CMD_DELETE_FILE and len(args) == 1:
        result = delete_file(sock, args[0])
    elif cmd == CMD_FILE_INFO and len(args) == 1:
        result = get_file_info(sock, args[0])
    elif cmd == CMD_REPLICATE_FILE and len(args) == 2:
        result = replicate_file(sock, args[0], args[1])
    elif cmd == CMD_PING_AS_NAMING and len(args) == 0:
        result = ping_as_naming(sock)
    else:
        logger.info('unrecognized command %d' % cmd)

    sock.close()
    return result
