import socket
import uuid
from threading import Thread

from constants import PING_SERVERS_SECONDS, NAMING_SERVER_PORT, STORAGE_SERVER_STARTING_PORT
from naming_server_directories import get_prev, delete_directory, reset_directories, get_last, directories, \
    check_directory, read_directory, make_directory, Directory
from receiver import receive_str, receive_int64, receive_int32
from sender import send_int32, send_str
from status_codes import CMD_PING_AS_NAMING, CODE_OK, ERR_FILE_NOT_EXIST, ERR_FILE_DIR_NOT_EXIST, ERR_DIR_NOT_EXIST, \
    CMD_REPLICATE_FILE, CODE_DIRECTORY_NOT_EXIST, CODE_FILE_NOT_EXIST, CMD_COPY_FILE, CMD_DELETE_FILE, CMD_INIT, \
    CMD_PING_AS_STORAGE, CMD_GET_STORAGE, CMD_WRITE_FILE, CMD_READ_FILE, CMD_CONFIRM_FILE_UPLOAD, CMD_FILE_INFO, \
    CMD_FILE_MOVE, CMD_CHECK_DIR, CMD_READ_DIR, CMD_MAKE_DIR, CMD_DELETE_DIR
from storage_server_client import send_command_to_storage_server
import threading
import time
from logs import logger, initialize_logs

clients = []

storage = []

write_file_map = {}


class File:
    def __init__(self, name: str, size: int):
        self.name = name
        self.size = size
        self.id = str(uuid.uuid4())


def ping_storage():
    while True:
        available_storage = []
        for st in storage:
            if not send_command_to_storage_server(st, CMD_PING_AS_NAMING, []):
                logger.info('lost %d' % st)
                storage.remove(st)
            else:
                available_storage.append(st)
        logger.info('available storage: %s' % str(available_storage))
        time.sleep(PING_SERVERS_SECONDS)


def get_directory_from_full_file_name(file_name: str):
    if len(file_name.split('/')) == 1:
        return ''
    return get_prev(file_name)


def initialize():
    delete_directory('', True)
    reset_directories()
    return CODE_OK


def file_info(file_path: str):
    file_dir = get_prev(file_path)
    file_name = get_last(file_path)
    if file_dir in directories:
        if file_name in directories[file_dir].files:
            f = directories[file_dir].files[file_name]
            ret = 'name: {}, size{} bytes, id: {}'.format(f.name, str(f.size), f.id)
            return ret
        else:
            return ERR_FILE_NOT_EXIST
    else:
        return ERR_FILE_DIR_NOT_EXIST


def move_file(file_path: str, new_dir: str):
    file_dir = get_prev(file_path)
    file_name = get_last(file_path)
    if file_dir in directories:
        if file_name in directories[file_dir].files:
            if not (new_dir in directories):
                return ERR_DIR_NOT_EXIST
            directories[new_dir].files[file_name] = directories[file_dir].files[file_name]
            del directories[file_dir].files[file_name]
            return CODE_OK
        else:
            return ERR_FILE_NOT_EXIST
    else:
        return ERR_FILE_DIR_NOT_EXIST


class ClientListener(Thread):

    def __init__(self, sock: socket.socket):
        super().__init__(daemon=True)
        self.sock = sock

    def _close(self):
        clients.remove(self.sock)
        self.sock.close()
        # logger.info(self.name + ' disconnected')

    def get_storage(self):
        send_int32(self.sock, len(storage))
        for i in range(len(storage)):
            send_int32(self.sock, storage[i])

    def ping_as_storage(self):
        port = STORAGE_SERVER_STARTING_PORT + len(storage)
        send_int32(self.sock, STORAGE_SERVER_STARTING_PORT + len(storage))
        storage.append(port)
        logger.info('%d storage connected' % port)

        for d in directories.values():
            for f in d.files.values():
                send_command_to_storage_server(port, CMD_REPLICATE_FILE, [storage[0], f.id])

    ''' Files Section '''

    def confirm_file_upload(self):
        try:
            port = receive_int32(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            return

        try:
            file_id = receive_str(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            return

        if file_id not in write_file_map:
            logger.info('file id is not in write_file_map')
            return

        file, directory = write_file_map[file_id]
        directory.files[file.name] = file
        del write_file_map[file_id]
        logger.info('file "%s" confirmed' % file.name)

        for s in storage:
            if s != port:
                logger.info('sent request to %d to replicate file "%s" from %d' % (s, file_id, port))
                send_command_to_storage_server(s, CMD_REPLICATE_FILE, [port, file.id])

        send_int32(self.sock, CODE_OK)

    def write_file(self):
        try:
            full_file_name = receive_str(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            return

        try:
            file_size = receive_int64(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            return

        path_to_file = get_directory_from_full_file_name(full_file_name)

        if path_to_file not in directories:
            logger.info('directory %s does not exist' % path_to_file)
            send_int32(self.sock, CODE_DIRECTORY_NOT_EXIST)
            return

        directory = directories[path_to_file]
        file_name = get_last(full_file_name)

        if file_name in directory.files:
            file = directory.files[file_name]
        else:
            file = File(file_name, file_size)

        write_file_map[file.id] = file, directory

        send_int32(self.sock, CODE_OK)
        send_str(self.sock, file.id)

    def read_file(self):
        try:
            full_file_name = receive_str(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            return

        path_to_file = get_directory_from_full_file_name(full_file_name)

        if path_to_file not in directories:
            logger.info('directory %s does not exist' % path_to_file)
            send_int32(self.sock, CODE_DIRECTORY_NOT_EXIST)
            return

        directory = directories[path_to_file]
        file_name = get_last(full_file_name)

        if file_name not in directory.files:
            logger.info('file %s does not exist' % file_name)
            send_int32(self.sock, CODE_FILE_NOT_EXIST)
            return

        file = directory.files[file_name]

        send_int32(self.sock, CODE_OK)
        send_str(self.sock, file.id)

    def copy_file(self):
        try:
            full_source_file_name = receive_str(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            return

        try:
            full_destination_file_name = receive_str(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            return

        path_to_source_file = get_directory_from_full_file_name(full_source_file_name)
        path_to_destination_file = get_directory_from_full_file_name(full_destination_file_name)

        if path_to_source_file not in directories:
            logger.info('directory %s does not exist' % path_to_source_file)
            send_int32(self.sock, CODE_DIRECTORY_NOT_EXIST)
            return

        if path_to_destination_file not in directories:
            logger.info('directory %s does not exist' % path_to_destination_file)
            send_int32(self.sock, CODE_DIRECTORY_NOT_EXIST)
            return

        source_directory = directories[path_to_source_file]
        destination_directory = directories[path_to_source_file]

        source_file_name = get_last(full_source_file_name)
        destination_file_name = get_last(full_destination_file_name)

        if source_file_name not in source_directory.files:
            logger.info('file %s does not exist' % source_file_name)
            send_int32(self.sock, CODE_FILE_NOT_EXIST)
            return

        source_file = source_directory.files[source_file_name]

        if destination_file_name in destination_directory.files:
            destination_file = destination_directory.files[destination_file_name]
        else:
            destination_file = File(destination_file_name, source_file.size)
            destination_directory.files[destination_file_name] = destination_file

        for s in storage:
            send_command_to_storage_server(s, CMD_COPY_FILE, [source_file.id, destination_file.id])

        send_int32(self.sock, CODE_OK)

    def delete_file(self):
        try:
            full_file_name = receive_str(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            return
        path_to_file = get_directory_from_full_file_name(full_file_name)
        if path_to_file not in directories:
            logger.info('directory %s does not exist' % path_to_file)
            send_int32(self.sock, CODE_DIRECTORY_NOT_EXIST)
            return
        d = directories[path_to_file]
        file_name = get_last(full_file_name)
        if file_name not in d.files:
            logger.info('file %s does not exist' % file_name)
            send_int32(self.sock, CODE_FILE_NOT_EXIST)
            return
        file = d.files[file_name]
        del d.files[file_name]
        for s in storage:
            send_command_to_storage_server(s, CMD_DELETE_FILE, [file.id])
        send_int32(self.sock, CODE_OK)

    def run(self):
        try:
            cmd = receive_int32(self.sock)
        except Exception as ex:
            logger.info(str(ex))
            self._close()
            return

        logger.info("received %d" % cmd)

        if cmd == CMD_INIT:
            ret = initialize()
            send_str(self.sock, ret)
        elif cmd == CMD_PING_AS_STORAGE:
            self.ping_as_storage()
        elif cmd == CMD_GET_STORAGE:
            self.get_storage()
        elif cmd == CMD_WRITE_FILE:
            self.write_file()
        elif cmd == CMD_READ_FILE:
            self.read_file()
        elif cmd == CMD_COPY_FILE:
            self.copy_file()
        elif cmd == CMD_CONFIRM_FILE_UPLOAD:
            self.confirm_file_upload()
        elif cmd == CMD_FILE_INFO:
            file_path = receive_str(self.sock)
            ret = file_info(file_path)
            send_str(self.sock, ret)
        elif cmd == CMD_FILE_MOVE:
            file_path = receive_str(self.sock)
            new_dir = receive_str(self.sock)
            ret = move_file(file_path, new_dir)
            send_str(self.sock, ret)
        elif cmd == CMD_DELETE_FILE:
            self.delete_file()
        elif cmd == CMD_CHECK_DIR:
            directory_path = receive_str(self.sock)
            ret = check_directory(directory_path)
            send_str(self.sock, ret)
        elif cmd == CMD_READ_DIR:
            directory_path = receive_str(self.sock)
            ret = read_directory(directory_path)
            send_str(self.sock, ret)
        elif cmd == CMD_MAKE_DIR:
            directory_path = receive_str(self.sock)
            ret = make_directory(directory_path)
            send_str(self.sock, ret)
        elif cmd == CMD_DELETE_DIR:
            directory_path = receive_str(self.sock)
            force = receive_str(self.sock)
            ret = delete_directory(directory_path, force)
            send_str(self.sock, ret)
        else:
            logger.info('error reading command code %d' % cmd)

        self._close()


def main():
    directories[''] = Directory('')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', NAMING_SERVER_PORT))
    sock.listen()

    threading.Thread(target=ping_storage).start()

    while True:
        logger.info('naming server listening for client')
        con, address = sock.accept()
        clients.append(con)
        logger.info('client connected from %s:%s' % (str(address[0]), str(address[1])))
        client_listener = ClientListener(con)
        client_listener.start()


if __name__ == "__main__":
    initialize_logs('naming_server_logs.txt')
    try:
        main()
    except Exception as e:
        logger.info(str(e))
