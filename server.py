import os
import shutil
import socket
from threading import Thread

from constants import BUFFER_SIZE
from receiver import receive_file_name, receive_file
from sender import send_file
from status_codes import *
from web_format_converter import int64_to_web, web_to_int, int32_to_web

clients = []


class ClientListener(Thread):
    def __init__(self, name: str, sock: socket.socket):
        super().__init__(daemon=True)
        self.sock = sock
        self.name = name

    def _close(self):
        clients.remove(self.sock)
        self.sock.close()
        print(self.name + ' disconnected')

    def copy_file(self):
        try:
            old_file_name = receive_file_name(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return

        try:
            new_file_name = receive_file_name(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return

        shutil.copyfile(old_file_name, new_file_name)

    def write_file(self):
        try:
            file_name = receive_file_name(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return

        try:
            receive_file(self.sock, file_name)
        except Exception as e:
            print(str(e))
            self._close()
            return

    def read_file(self):
        try:
            file_name = receive_file_name(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return

        if not os.path.isfile(file_name):
            self.sock.send(int32_to_web(CODE_FILE_NOT_EXIST))
            self._close()
            print('Error: file does not exist')
            return
        else:
            self.sock.send(int32_to_web(CODE_OK))

        send_file(self.sock, file_name)

    def run(self):
        command_code = web_to_int(self.sock.recv(32))

        if command_code == CODE_WRITE_FILE:
            self.write_file()
        elif command_code == CODE_READ_FILE:
            self.read_file()
        elif command_code == CODE_COPY_FILE:
            self.copy_file()
        else:
            print('Error reading command code.')
        self.sock.close()


def main():
    next_name = 1

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 8800))
    sock.listen()

    while True:
        con, addr = sock.accept()
        clients.append(con)
        name = 'u' + str(next_name)
        next_name += 1
        print(str(addr) + ' connected as ' + name)
        ClientListener(name, con).start()


if __name__ == "__main__":
    main()
