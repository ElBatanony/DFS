import os
import socket
from threading import Thread

clients = []
files = set()


class ClientListener(Thread):
    def __init__(self, name: str, sock: socket.socket):
        super().__init__(daemon=True)
        self.sock = sock
        self.name = name

    def _close(self):
        clients.remove(self.sock)
        self.sock.close()
        print(self.name + ' disconnected')

    @staticmethod
    def _get_file_name(name):
        name_parts = name.split('.')
        index = 1
        while name in files:
            name = name_parts[0] + '_copy' + str(index) + '.' + name_parts[1]
            index += 1
        files.add(name)
        return name

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
        file_name = ClientListener._get_file_name(file_name)

        with open(file_name, 'wb') as sw:

            received_size = 0

            while received_size < file_size:
                buffer = min(file_size - received_size, 1024)
                file = self.sock.recv(buffer)
                received_size += buffer
                if file is None:
                    self._close()
                    print('Error during file transfer.')
                    return
                sw.write(file)

            print(file_name + ' received.')


def main():
    for file in os.listdir():
        files.add(file)

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