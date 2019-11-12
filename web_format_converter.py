def int64_to_web(value):
    return int.to_bytes(value, byteorder='big', length=64, signed=False)


def int32_to_web(value):
    return int.to_bytes(value, byteorder='big', length=32, signed=False)


def web_to_int(value):
    return int.from_bytes(value, byteorder='big', signed=False)
