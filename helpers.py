import socket
import os
from constants_and_codes import *

def int64_to_web(value): return int.to_bytes(value, byteorder='big', length=64, signed=False)
def int32_to_web(value): return int.to_bytes(value, byteorder='big', length=32, signed=False)
def web_to_int(value): return int.from_bytes(value, byteorder='big', signed=False)

# Opens a socket to a given ip and port
def open_socket(ip, port): 
    try :
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(5) # make longer for large uploads
        sock.connect((ip, port))
        return sock
    except Exception as e:
        print('Can not open connection to ' + ip + ':' + str(port) )
        return False

def send_int32(sock, value): sock.send(int32_to_web(value))
def send_int64(sock, value): sock.send(int32_to_web(value))
def send_code(sock,value): send_int32(sock,value)
def receive_int32(sock): return web_to_int(sock.recv(32))
def receive_int64(sock): return web_to_int(sock.recv(64))
def receive_code(sock): return receive_int32(sock)

def send_str(sock, value):
    value = str(value)
    encoded_value = value.encode('UTF-8')
    sock.send(int32_to_web(len(encoded_value)))
    sock.send(encoded_value)

def receive_str(sock):
    txt_size = web_to_int(sock.recv(32))
    if txt_size is None: raise Exception('String to send is None!')
    txt = sock.recv(txt_size).decode('UTF-8')
    if txt is None: raise Exception('String received is None!')
    return txt

def send_file(sock, file_path):
    file_size = os.path.getsize(file_path)
    sock.send(int64_to_web(file_size))

    sent_file_size = 0
    if file_size == 0:
        print('Sending empty file. Could cause problems!')
        #return

    with open(file_path, 'rb') as sr:
        while sent_file_size <= file_size:
            sock.send(sr.read(BUFFER_SIZE))
            sent_file_size += BUFFER_SIZE

            percentage = int(100 * sent_file_size / file_size)
            if percentage > 100:
                percentage = 100
            print('Uploaded ' + str(percentage) + '%')

    print('File sent!')

def receive_file(sock, file_path):
    file_size = web_to_int(sock.recv(64))
    if file_size is None: raise Exception('File size to receive is None!')

    with open(file_path, 'wb') as sw:
        received_size = 0
        while received_size < file_size:
            buffer = min(file_size - received_size, BUFFER_SIZE)
            f = sock.recv(buffer)
            received_size += buffer
            if f is None:
                raise Exception('error during file transfer')
            sw.write(f)

    print('File received!')
