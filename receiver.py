from constants import BUFFER_SIZE
from web_format_converter import web_to_int


def receive_str(sock):
    value_size = web_to_int(sock.recv(32))
    if value_size is None:
        raise Exception('error during string size reading')

    value = sock.recv(value_size).decode('UTF-8')
    if value is None or value == '':
        raise Exception('error during string reading')

    return value


def receive_file(sock, file_name):
    file_size = web_to_int(sock.recv(64))

    if file_size is None:
        raise Exception('error during file size reading')

    with open(file_name, 'wb') as sw:

        received_size = 0

        while received_size < file_size:
            buffer = min(file_size - received_size, BUFFER_SIZE)
            file = sock.recv(buffer)
            received_size += buffer
            if file is None:
                raise Exception('error during file transfer')
            sw.write(file)

    print('%s received' % file_name)