import os
import socket
from threading import Thread

from constants import BUFFER_SIZE
from status_codes import *

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

    def read_file(self):
        file_name_size = int.from_bytes(bytes=self.sock.recv(32), byteorder='big', signed=False)
        if file_name_size is None:
            self._close()
            print('Error during file name size reading.')
            return

        file_name = self.sock.recv(file_name_size).decode('UTF-8')
        if file_name is None:
            self._close()
            print('Error during file name reading.')

        if not os.path.isfile(file_name):
            self.sock.send(CODE_FILE_NOT_EXIST)
            self._close()
            print('Error: file does not exist')
            return
        else:
            self.sock.send(CODE_OK)

        file_size = os.path.getsize(file_name)
        self.sock.send(int.to_bytes(file_size, byteorder='big', length=64, signed=False))

        with open(file_name, 'rb') as sr:

            received_size = 0

            while received_size < file_size:
                buffer = min(file_size - received_size, BUFFER_SIZE)
                file = self.sock.send(sr.read(buffer))
                received_size += buffer
                if file is None:
                    self._close()
                    print('Error during file transfer.')
                    return
                sw.write(file)

            print(file_name + ' received.')

    def run(self):
        file_name_size = int.from_bytes(bytes=self.sock.recv(32), byteorder='big', signed=False)

        if file_name_size is None:
            self._close()
            print('Error during file name size reading.')
            return

        file_size = int.from_bytes(bytes=self.sock.recv(64), byteorder='big', signed=False)

        if file_size is None:
            self._close()
            print('Error during file size reading.')
            return

        file_name = self.sock.recv(file_name_size).decode('UTF-8')

        with open(file_name, 'wb') as sw:

            received_size = 0

            while received_size < file_size:
                buffer = min(file_size - received_size, BUFFER_SIZE)
                file = self.sock.recv(buffer)
                received_size += buffer
                if file is None:
                    self._close()
                    print('Error during file transfer.')
                    return
                sw.write(file)

            print(file_name + ' received.')


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
