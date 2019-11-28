import os
import shutil
import socket
from threading import Thread

from constants import STORAGE_SERVER_ROOT_PATH
from logs import initialize_logs, logger
from naming_server_client import send_command_to_naming_server
from receiver import receive_str, receive_file, receive_int32
from sender import send_int32, send_file
from status_codes import CMD_READ_FILE, CODE_OK, CODE_FILE_NOT_EXIST, CMD_CONFIRM_FILE_UPLOAD, CMD_WRITE_FILE, \
    CMD_COPY_FILE, CMD_DELETE_FILE, CMD_REPLICATE_FILE, CMD_PING_AS_NAMING, CMD_PING_AS_STORAGE
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
        logger.info('received replication command')
        try:
            p = receive_int32(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            self._close()
            return
        try:
            file_name = receive_str(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            self._close()
            return
        logger.info('received command to replicate file "%s" from %d' % (file_name, p))
        send_command_to_storage_server(p, CMD_READ_FILE, [file_name, file_name, STORAGE_SERVER_ROOT_PATH])
        send_int32(self.sock, CODE_OK)

    def ping_as_naming(self):
        send_int32(self.sock, CODE_OK)

    def delete_file(self):
        try:
            file_name = receive_str(self.sock)
        except Exception as ex:
            logger.info(str(ex))
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
        except Exception as ex:
            logger.info(str(ex))
            self._close()
            return

        try:
            new_file_name = receive_str(self.sock)
        except Exception as ex:
            logger.info(str(ex))
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
        except Exception as ex:
            logger.info(str(ex))
            self._close()
            return
        try:
            receive_file(self.sock, file_name, STORAGE_SERVER_ROOT_PATH)
        except Exception as ex:
            logger.info(str(ex))
            self._close()
            return
        send_int32(self.sock, CODE_OK)
        send_command_to_naming_server(CMD_CONFIRM_FILE_UPLOAD, [port, file_name])

    def read_file(self):
        try:
            file_name = receive_str(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            self._close()
            return

        if not os.path.isfile(os.path.join(STORAGE_SERVER_ROOT_PATH, file_name)):
            self.sock.send(int32_to_web(CODE_FILE_NOT_EXIST))
            self._close()
            logger.info('error: file "%s" does not exist' % file_name)
            return
        else:
            self.sock.send(int32_to_web(CODE_OK))

        send_file(self.sock, file_name, STORAGE_SERVER_ROOT_PATH)

    def run(self):
        try:
            command_code = receive_int32(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            self.sock.close()
            return

        logger.info('received %d from %s' % (command_code, self.name))

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


port = 0


def main():
    global port
    if not os.path.isdir(STORAGE_SERVER_ROOT_PATH):
        os.mkdir(STORAGE_SERVER_ROOT_PATH)

    port = send_command_to_naming_server(CMD_PING_AS_STORAGE, [])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
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
