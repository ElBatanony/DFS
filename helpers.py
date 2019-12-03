import socket

from constants_and_codes import *


def int32_to_web(value): return int.to_bytes(value, byteorder='big', length=32, signed=False)


def web_to_int(value): return int.from_bytes(value, byteorder='big', signed=False)


# Opens a socket to a given ip and port
def open_socket(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sock.settimeout(10) # make longer for large uploads
        sock.connect((ip, port))
        return sock
    except Exception as e:
        print('Can not open connection to ' + ip + ':' + str(port))
        return False


def send_int32(sock, value): sock.send(int32_to_web(value))


def send_code(sock, value): send_int32(sock, value)


def receive_int32(sock): return web_to_int(sock.recv(32))


def receive_code(sock): return receive_int32(sock)


def send_str(sock, value):
    value = str(value)
    encoded_value = value.encode('UTF-8')
    send_int32(sock, len(encoded_value))
    sock.send(encoded_value)


def receive_str(sock):
    txt_size = receive_int32(sock)
    if txt_size is None: raise Exception('String to send is None!')
    txt = sock.recv(txt_size).decode('UTF-8')
    if txt is None: raise Exception('String received is None!')
    return txt


def send_file(sock, file_path):
    file_size = os.path.getsize(file_path)
    send_int32(sock, file_size)

    sent_file_size = 0

    if file_size == 0:
        return

    with open(file_path, 'rb') as sr:
        while sent_file_size < file_size:
            buffer = min(file_size - sent_file_size, BUFFER_SIZE)
            sock.send(sr.read(buffer))
            if receive_int32(sock) != CODE_OK:
                print('received not ok')
            sent_file_size += buffer

            percentage = int(100 * sent_file_size / file_size)
            if percentage > 100:
                percentage = 100

            print('Uploading ' + str(percentage) + '%', end='\r')

    print('%s sent' % file_path)


def receive_file(sock, file_path):
    file_size = receive_int32(sock)

    if file_size is None:
        raise Exception('error during file size reading')

    with open(file_path, 'wb') as sw:

        received_size = 0

        while received_size < file_size:
            buffer = min(file_size - received_size, BUFFER_SIZE)
            file = sock.recv(buffer)
            received_size += buffer
            send_int32(sock, CODE_OK)
            percentage = int(100 * received_size / file_size)
            print('Downloading ' + str(percentage) + '%', end='\r')
            if file is None:
                raise Exception('error during file transfer')
            sw.write(file)
