import os

from constants import BUFFER_SIZE
from web_format_converter import int32_to_web, int64_to_web


def send_str(sock, value):
    value = str(value)
    encoded_value = value.encode('UTF-8')
    sock.send(int32_to_web(len(encoded_value)))
    sock.send(encoded_value)


def send_int32(sock, value):
    sock.send(int32_to_web(value))


def send_int64(sock, value):
    sock.send(int32_to_web(value))


def send_file(sock, file_name):
    file_size = os.path.getsize(file_name)
    sock.send(int64_to_web(file_size))

    sent_file_size = 0

    if file_size == 0:
        return

    with open(file_name, 'rb') as sr:
        print(file_name)
        while sent_file_size <= file_size:
            sock.send(sr.read(BUFFER_SIZE))
            sent_file_size += BUFFER_SIZE

            percentage = int(100 * sent_file_size / file_size)
            if percentage > 100:
                percentage = 100

            print(str(percentage) + '%')

    print('%s sent' % file_name)
