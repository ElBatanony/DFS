import os
import socket

from constants import BUFFER_SIZE
from logs import logger
from web_format_converter import web_to_int


def receive_str(sock: socket.socket):
    value_size = web_to_int(sock.recv(32))
    if value_size is None:
        raise Exception('error during string size reading')

    value = sock.recv(value_size).decode('UTF-8')
    if value is None:
        raise Exception('error during string reading')

    return str(value)


def receive_int32(sock: socket.socket):
    return web_to_int(sock.recv(32))


def receive_int64(sock: socket.socket):
    return web_to_int(sock.recv(64))


def receive_file(sock: socket.socket, file_name: str, root_dir: str):
    file_size = web_to_int(sock.recv(64))

    if file_size is None:
        raise Exception('error during file size reading')

    with open(os.path.join(root_dir, file_name), 'wb') as sw:

        received_size = 0

        while received_size < file_size:
            buffer = min(file_size - received_size, BUFFER_SIZE)
            file = sock.recv(buffer)
            received_size += buffer
            if file is None:
                raise Exception('error during file transfer')
            sw.write(file)

    logger.info('%s received' % file_name)
