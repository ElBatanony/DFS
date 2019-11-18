import os
import shutil
import socket
from threading import Thread
import time
import stat

from constants import *
from logs import initialize_logs, logger
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
        self.sock.close()
        logger.info(self.name + ' disconnected')

    def replicate_file(self):
        try:
            source_address = receive_str(self.sock)
        except Exception as e:
            logger.info(str(e))
            self._close()
            return
        try:
            file_name = receive_str(self.sock)
        except Exception as e:
            logger.info(str(e))
            self._close()
            return
        send_command_to_storage_server(source_address, CMD_READ_FILE, [file_name, file_name, STORAGE_SERVER_ROOT_PATH])
        send_int32(self.sock, CODE_OK)

    def ping_as_naming(self):
        send_int32(self.sock, CODE_OK)

    def delete_file(self):
        try:
            file_name = receive_str(self.sock)
        except Exception as e:
            logger.info(str(e))
            self._close()
            return

        if os.path.exists(os.path.join(STORAGE_SERVER_ROOT_PATH, file_name)):
            os.remove(os.path.join(STORAGE_SERVER_ROOT_PATH, file_name))
            self.sock.send(int32_to_web(CODE_OK))
            logger.info("file {0} removed.".format(file_name))
        else:
            self.sock.send(int32_to_web(CODE_FILE_NOT_EXIST))
            logger.info('error: no such file')
            return

    def copy_file(self):
        try:
            old_file_name = receive_str(self.sock)
        except Exception as e:
            logger.info(str(e))
            self._close()
            return

        try:
            new_file_name = receive_str(self.sock)
        except Exception as e:
            logger.info(str(e))
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
            logger.info(str(e))
            self._close()
            return
        try:
            receive_file(self.sock, file_name, STORAGE_SERVER_ROOT_PATH)
        except Exception as e:
            logger.info(str(e))
            self._close()
            return
        send_int32(self.sock, CODE_OK)
        send_command_to_naming_server(CMD_CONFIRM_FILE_UPLOAD, [file_name])

    def read_file(self):
        try:
            file_name = receive_str(self.sock)
        except Exception as e:
            logger.info(str(e))
            self._close()
            return

        if not os.path.isfile(os.path.join(STORAGE_SERVER_ROOT_PATH, file_name)):
            self.sock.send(int32_to_web(CODE_FILE_NOT_EXIST))
            self._close()
            logger.info('error: file does not exist')
            return
        else:
            self.sock.send(int32_to_web(CODE_OK))

        send_file(self.sock, file_name, STORAGE_SERVER_ROOT_PATH)

    def run(self):
        command_code = web_to_int(self.sock.recv(32))

        logger.info('Received ' + str(command_code) + ' from ' + self.name)

        if command_code == CMD_WRITE_FILE:
            self.write_file()
        elif command_code == CMD_READ_FILE:
            self.read_file()
        elif command_code == CMD_COPY_FILE:
            self.copy_file()
        elif command_code == CMD_DELETE_FILE:
            self.delete_file()
        elif command_code == CMD_REPLICATE_FILE:
            self.replicate_file()
        elif command_code == CMD_PING_AS_NAMING:
            self.ping_as_naming()
        else:
            logger.info('error reading command code %d' % command_code)
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
    initialize_logs('storage_server_logs.txt')
    try:
        main()
    except Exception as e:
        logger.info(str(e))
