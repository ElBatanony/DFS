import os
import socket
import sys

from constants import BUFFER_SIZE


def main():
    host = sys.argv[len(sys.argv) - 2]
    port = int(sys.argv[len(sys.argv) - 1])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, port))

    for i in range(1, len(sys.argv) - 2):
        file_name = sys.argv[i]
        encoded_file_name = file_name.encode('UTF-8')

        # if not os.path.exists(file_name):
        #     print(file_name)
        #     print('File does not exist.')
        #     return

        file_size = os.path.getsize(file_name)
        encoded_file_name_size = len(encoded_file_name)

        sock.send(int.to_bytes(encoded_file_name_size, byteorder='big', length=32, signed=False))
        sock.send(int.to_bytes(file_size, byteorder='big', length=64, signed=False))
        sock.send(encoded_file_name)

        sent_file_size = 0

        # with open(file_name, 'rb') as sr:
        #     print(file_name)
        #     while sent_file_size <= file_size:
        #         sock.send(sr.read(BUFFER_SIZE))
        #         sent_file_size += BUFFER_SIZE
        #
        #         percentage = int(100 * sent_file_size / file_size)
        #         if percentage > 100:
        #             percentage = 100
        #
        #         print(str(percentage) + '%')


if __name__ == "__main__":
    main()
