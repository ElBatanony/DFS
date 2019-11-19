import socket

from constants import *
from status_codes import *
from receiver import *
from sender import *
from requests import get


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


def get_ip():
    return get('https://api.ipify.org').text


def ping_as_storage(sock):
    send_int32(sock, CMD_PING_AS_STORAGE)
    ip = get_ip()
    send_str(sock, ip)
    try:
        code = receive_int32(sock)
    except Exception as e:
        logger.info(str(e))
        return False
    if code != CODE_OK:
        logger.info('error with code %d' % code)
        return False
    logger.info('ping is successful')
    return True


def confirm_file_upload(sock, file_id):
    send_int32(sock, CMD_CONFIRM_FILE_UPLOAD)
    ip = get_ip()
    send_str(sock, ip)
    send_str(sock, file_id)
    try:
        code = receive_int32(sock)
    except Exception as e:
        logger.info(str(e))
        return False
    if code != CODE_OK:
        return False
    return True


def get_storage(sock):
    send_int32(sock, CMD_GET_STORAGE)
    size = receive_int32(sock)
    storage = []
    for i in range(size):
        try:
            storage.append(receive_str(sock))
        except Exception as e:
            logger.info(str(e))
            return False

    logger.info('received storage: %s' % str(storage))
    return storage


def write_file(sock, file_name):
    if not os.path.exists(os.path.join(CLIENT_ROOT_PATH, file_name)):
        logger.info('error "file does not exist" received after sending "write_file" from naming server client')
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


def read_file(sock, file_name):
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


def copy_file(sock, source_file_name, destination_file_name):
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


def open_directory(sock, directory_name):
    send_int32(sock, CMD_OPEN_DIR)
    send_str(sock, directory_name)
    ret = receive_str(sock)
    logger.info('cd response: ' + ret)


def read_directory(sock):
    send_int32(sock, CMD_READ_DIR)
    dir = receive_str(sock)
    logger.info('ls response: ' + dir)


def make_directory(sock, directory_name):
    send_int32(sock, CMD_MAKE_DIR)
    send_str(sock, directory_name)
    ret = receive_str(sock)
    logger.info('mkdir response: ' + ret)


def delete_directory(sock, directory_name):
    send_int32(sock, CMD_DELETE_DIR)
    send_str(sock, directory_name)
    ret = receive_str(sock)
    logger.info('rmdir response: ' + ret)


def init_server(sock):
    send_int32(sock, CMD_INIT)
    ret = receive_str(sock)
    logger.info('init response: ' + ret)


def file_info(sock, file_name):
    send_int32(sock, CMD_FILE_INFO)
    send_str(sock, file_name)
    ret = receive_str(sock)
    logger.info('info response: ' + ret)


def move_file(sock, file_name, new_path):
    send_int32(sock, CMD_FILE_MOVE)
    send_str(sock, file_name)
    send_str(sock, new_path)
    ret = receive_str(sock)
    logger.info('mv response: ' + ret)


def send_command_to_naming_server(cmd: int, args):
    host = NAMING_SERVER_IP
    port = NAMING_SERVER_PORT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, port))

    result = None
    if cmd == CMD_CONFIRM_FILE_UPLOAD and len(args) == 1:
        result = confirm_file_upload(sock, args[0])
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
        result = open_directory(sock, args[0])
    elif cmd == CMD_READ_DIR and len(args) == 0:
        result = read_directory(sock)
    elif cmd == CMD_MAKE_DIR and len(args) == 1:
        result = make_directory(sock, args[0])
    elif cmd == CMD_DELETE_DIR and len(args) == 1:
        result = delete_directory(sock, args[0])
    elif cmd == CMD_INIT and len(args) == 0:
        result = init_server(sock)
    elif cmd == CMD_FILE_INFO and len(args) == 1:
        result = file_info(sock, args[0])
    elif cmd == CMD_FILE_MOVE and len(args) == 2:
        result = move_file(sock, args[0], args[1])
    elif cmd == CMD_PING_AS_STORAGE and len(args) == 0:
        result = ping_as_storage(sock)
    else:
        logger.info('Command-arguments combination unrecognized')

    sock.close()
    return result
