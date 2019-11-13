from web_format_converter import int32_to_web, int64_to_web, web_to_int

def send_str(sock, txt):
    encoded_txt = encode(txt)
    encoded_txt_size = len(encoded_txt)
    sock.send(int32_to_web(encoded_txt_size))
    sock.send(encoded_txt)

def recv_str(sock):
    encoded_txt_size = web_to_int(sock.recv(32))
    decoded_txt = decode( sock.recv(encoded_txt_size) )
    return decoded_txt

def encode(txt):
    return txt.encode('UTF-8')

def decode(bytes):
    return bytes.decode('UTF-8')
