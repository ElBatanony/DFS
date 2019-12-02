import os

from constants import BUFFER_SIZE
from logs import logger
from web_format_converter import int32_to_web, int64_to_web


def send_str(sock, value):
    value = str(value)
    encoded_value = value.encode('UTF-8')
    sock.send(int32_to_web(len(encoded_value)))
    sock.send(encoded_value)


def send_int32(sock, value):
    sock.send(int32_to_web(value))


def send_int64(sock, value):
    sock.send(int64_to_web(value))


def send_file(sock, file_name, root_dir):
    file_size = os.path.getsize(os.path.join(root_dir, file_name))
    sock.send(int64_to_web(file_size))

    sent_file_size = 0

    if file_size == 0:
        return

    with open(os.path.join(root_dir, file_name), 'rb') as sr:
        while sent_file_size < file_size:
            buffer = min(file_size - sent_file_size, BUFFER_SIZE)
            sock.send(sr.read(buffer))
            sent_file_size += buffer

            percentage = int(100 * sent_file_size / file_size)
            if percentage > 100:
                percentage = 100

            logger.info(str(percentage) + '%')

    logger.info('%s sent' % file_name)
