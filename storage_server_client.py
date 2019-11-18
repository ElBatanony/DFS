import socket

from constants import *
from receiver import *
from sender import *
from status_codes import *

def ping_as_naming(sock):
    send_int32(sock, CMD_PING_AS_NAMING)
    ret = receive_int32(sock)
    if ret != CODE_OK:
        return False
    return True

def replicate_file(sock: socket.socket, address: str, file_name: str):
    send_int32(sock, CMD_REPLICATE_FILE)
    send_str(sock, address)
    send_str(sock, file_name)
    code = receive_int32(sock)
    if code != CODE_OK:
        print('error with code %d' % code)
        return False
    return True


def get_file_info(sock: socket.socket, file_name):
    send_int32(sock, CMD_FILE_INFO)
    send_str(sock, file_name)
    code = receive_int32(sock)
    if code != CODE_OK:
        print('error with code %d' % code)
        return False
    file_info = receive_str(sock)
    print(file_info)
    return True


def delete_file(sock, file_name):
    send_int32(sock, CMD_DELETE_FILE)
    send_str(sock, file_name)
    code = receive_int32(sock)
    if code != CODE_OK:
        print('error with code %d' % code)
        return False
    print('file removed')
    return True


def copy_file(sock, old_file_name, new_file_name):
    send_int32(sock, CMD_COPY_FILE)
    send_str(sock, old_file_name)
    send_str(sock, new_file_name)
    code = receive_int32(sock)
    if code != CODE_OK:
        print('error with code %d' % code)
        return False
    print('file copied')
    return True


def read_file(sock: socket.socket, path_to_source_file: str, path_to_destination_file: str):
    send_int32(sock, CMD_READ_FILE)
    send_str(sock, path_to_source_file)
    code = receive_int32(sock)
    if code != CODE_OK:
        print('error with code %d' % code)
        return False
    try:
        receive_file(sock, path_to_destination_file, CLIENT_ROOT_PATH)
    except Exception as e:
        print(str(e))
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
        print(str(e))
        return False
    if code != CODE_OK:
        print('error with code %d' % str(code))
        return False
    return True


def send_command_to_storage_server(host: str, cmd: int, args=[]):
    port = STORAGE_SERVER_PORT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.connect((host, port))
    except Exception as e:
        print(str(e))
        return False

    result = None

    if cmd == CMD_WRITE_FILE and len(args) == 3:
        result = write_file(sock, args[0], args[1], args[2])
    elif cmd == CMD_READ_FILE and len(args) == 2:
        result = read_file(sock, args[0], args[1])
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
        print('unrecognized command')

    sock.close()
    return result


def get_command_from_str(cmd: str):
    if cmd == 'w':
        return CMD_WRITE_FILE
    elif cmd == 'r':
        return CMD_READ_FILE
    elif cmd == 'c':
        return CMD_COPY_FILE
    elif cmd == 'd':
        return CMD_DELETE_FILE
    elif cmd == 'n':
        return CMD_CREATE_EMPTY_FILE
    elif cmd == 'i':
        return CMD_FILE_INFO


def main():
    while True:
        args = input('Enter command:').split()
        try:
            send_command_to_storage_server('localhost', get_command_from_str(args[0]), args[1:])
        except Exception as e:
            print(str(e))


if __name__ == "__main__":
    main()
