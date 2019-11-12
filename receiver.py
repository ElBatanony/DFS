from constants import BUFFER_SIZE
from web_format_converter import web_to_int


def receive_file_name(sock):
    file_name_size = web_to_int(sock.recv(32))
    if file_name_size is None:
        raise Exception('Error during file name size reading.')

    file_name = sock.recv(file_name_size).decode('UTF-8')
    if file_name is None:
        raise Exception('Error during file name reading.')

    return file_name


def receive_file(sock, file_name):
    file_size = web_to_int(sock.recv(64))

    if file_size is None:
        raise Exception('Error during file size reading.')

    with open(file_name, 'wb') as sw:

        received_size = 0

        while received_size < file_size:
            buffer = min(file_size - received_size, BUFFER_SIZE)
            file = sock.recv(buffer)
            received_size += buffer
            if file is None:
                raise Exception('Error during file transfer.')
            sw.write(file)

    print('%s received.' % file_name)
