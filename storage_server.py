import os
import shutil
import socket
from threading import Thread
import time
import stat

from constants import *
from naming_server_client import send_command_to_naming_server
from receiver import *
from sender import *
from status_codes import *
from storage_server_client import send_command_to_storage_server
from web_format_converter import *


class ClientListener(Thread):
    def __init__(self, name: str, sock: socket.socket):
        super().__init__(daemon=True)
        self.sock = sock
        self.name = name

    def _close(self):
        clients.remove(self.sock)
        self.sock.close()
        print(self.name + ' disconnected')

    def replicate_file(self):
        try:
            source_address = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return
        try:
            file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return
        send_command_to_storage_server(source_address, CMD_READ_FILE, [file_name, file_name])
        send_int32(self.sock, CODE_OK)

    def get_file_info(self):
        try:
            file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return

        if os.path.exists(file_name):
            self.sock.send(int32_to_web(CODE_OK))

            info = os.stat(file_name)

            result = ''

            mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = info
            result += "\nFile '{0}' info:\n".format(file_name)
            result += "Size: {0} bytes.\n".format(size)
            result += "Last accessed: {0}.\n".format(time.asctime(time.localtime(atime)))
            result += "Last modified: {0}.\n".format(time.asctime(time.localtime(mtime)))
            result += "File info last changed: {0}.\n".format(time.asctime(time.localtime(ctime)))
            result += "Protection bits: {0}.\n".format(oct(stat.S_IMODE(mode))[2:])
            result += "Hardlinks number: {0}.\n".format(nlink)

            send_str(self.sock, result)
        else:
            self.sock.send(int32_to_web(CODE_FILE_NOT_EXIST))
            print('error: no such file')
            return

    def create_empty_file(self):
        try:
            file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return

        if os.path.exists(file_name):
            self.sock.send(int32_to_web(CODE_FILE_ALREADY_EXIST))
            print('error: file {0} already exists'.format(file_name))
            return
        else:
            open(file_name, 'a').close()
            self.sock.send(int32_to_web(CODE_OK))
            print("created {0} empty file".format(file_name))

    def delete_file(self):
        try:
            file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return

        if os.path.exists(file_name):
            os.remove(file_name)
            self.sock.send(int32_to_web(CODE_OK))
            print("file {0} removed.".format(file_name))
        else:
            self.sock.send(int32_to_web(CODE_FILE_NOT_EXIST))
            print('error: no such file')
            return

    def copy_file(self):
        try:
            old_file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return

        try:
            new_file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return

        if os.path.exists(os.path.join(STORAGE_SERVER_ROOT_PATH, old_file_name)):
            shutil.copyfile(os.path.join(STORAGE_SERVER_ROOT_PATH, old_file_name),
                            os.path.join(STORAGE_SERVER_ROOT_PATH, new_file_name))
            self.sock.send(int32_to_web(CODE_OK))
        else:
            self.sock.send(int32_to_web(CODE_FILE_NOT_EXIST))

    def write_file(self):
        try:
            file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return
        try:
            receive_file(self.sock, file_name, STORAGE_SERVER_ROOT_PATH)
        except Exception as e:
            print(str(e))
            self._close()
            return
        send_int32(self.sock, CODE_OK)
        send_command_to_naming_server(CMD_CONFIRM_FILE_UPLOAD, [file_name])

    def read_file(self):
        try:
            file_name = receive_str(self.sock)
        except Exception as e:
            print(str(e))
            self._close()
            return

        if not os.path.isfile(os.path.join(STORAGE_SERVER_ROOT_PATH, file_name)):
            self.sock.send(int32_to_web(CODE_FILE_NOT_EXIST))
            self._close()
            print('error: file does not exist')
            return
        else:
            self.sock.send(int32_to_web(CODE_OK))

        send_file(self.sock, file_name, STORAGE_SERVER_ROOT_PATH)

    def run(self):
        command_code = web_to_int(self.sock.recv(32))

        if command_code == CMD_WRITE_FILE:
            self.write_file()
        elif command_code == CMD_READ_FILE:
            self.read_file()
        elif command_code == CMD_COPY_FILE:
            self.copy_file()
        elif command_code == CMD_DELETE_FILE:
            self.delete_file()
        elif command_code == CMD_CREATE_EMPTY_FILE:
            self.create_empty_file()
        elif command_code == CMD_FILE_INFO:
            self.get_file_info()
        elif command_code == CMD_REPLICATE_FILE:
            self.replicate_file()
        else:
            print('error reading command code %d' % command_code)
        self.sock.close()


def main():
    if not os.path.isdir(STORAGE_SERVER_ROOT_PATH):
        os.mkdir(STORAGE_SERVER_ROOT_PATH)

    send_command_to_naming_server(CMD_PING_AS_STORAGE, [])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', STORAGE_SERVER_PORT))
    sock.listen()

    while True:
        connection, address = sock.accept()
        ClientListener(str(address[0]), connection).start()


if __name__ == "__main__":
    main()
