import os
import socket
import sys

from constants import BUFFER_SIZE
from status_codes import CODE_WRITE_FILE, CODE_READ_FILE, CODE_OK
from web_format_converter import int32_to_web, int64_to_web, web_to_int


def read_file(sock, file_name):
    encoded_file_name = file_name.encode('UTF-8')
    encoded_file_name_size = len(encoded_file_name)

    sock.send(int32_to_web(encoded_file_name_size))
    sock.send(encoded_file_name)

    code = web_to_int(sock.recv(32))

    if code != CODE_OK:
        sock.close()
        print('Error with code %d' % code)
        return

    file_size = web_to_int(sock.recv(64))

    with open(file_name, 'wb') as sw:

        received_size = 0

        while received_size < file_size:
            buffer = min(file_size - received_size, BUFFER_SIZE)
            file = sock.recv(buffer)
            received_size += buffer
            if file is None:
                sock.close()
                print('Error during file transfer.')
                return
            sw.write(file)

        print(file_name + ' received.')


def write_file(sock, file_name):
    encoded_file_name = file_name.encode('UTF-8')

    if not os.path.exists(file_name):
        print('File does not exist.')
        return

    file_size = os.path.getsize(file_name)
    encoded_file_name_size = len(encoded_file_name)

    sock.send(int32_to_web(encoded_file_name_size))
    sock.send(int64_to_web(file_size))
    sock.send(encoded_file_name)

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


def main():
    host = sys.argv[len(sys.argv) - 2]
    port = int(sys.argv[len(sys.argv) - 1])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, port))

    command = sys.argv[1]
    if command == 'w':
        sock.send(int32_to_web(CODE_WRITE_FILE))
        write_file(sock, sys.argv[2])
    elif command == 'r':
        sock.send(int32_to_web(CODE_READ_FILE))
        read_file(sock, sys.argv[2])

    sock.close()


if __name__ == "__main__":
    main()
