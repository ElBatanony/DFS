import os
import socket
import sys

from receiver import receive_file
from sender import send_file_name, send_file
from status_codes import CODE_WRITE_FILE, CODE_READ_FILE, CODE_OK
from web_format_converter import int32_to_web, int64_to_web, web_to_int


def read_file(sock, file_name):
    send_file_name(sock, file_name)

    code = web_to_int(sock.recv(32))

    if code != CODE_OK:
        sock.close()
        print('Error with code %d' % code)
        return

    try:
        receive_file(sock, file_name)
    except Exception as e:
        print(str(e))
        sock.close()
        return


def write_file(sock, file_name):
    if not os.path.exists(file_name):
        print('File does not exist.')
        return

    send_file_name(sock, file_name)
    send_file(sock, file_name)


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
