# Constants
import os
BUFFER_SIZE = 1024
INITIAL_SIZE = 4096
CLIENT_ROOT_PATH = "client_files"
STORAGE_SERVER_ROOT_PATH = "storage_server_files"
#NAMING_SERVER_IP = "localhost"
NAMING_SERVER_IP = "dfs.misr.app"
#NAMING_SERVER_IP = os.getenv('NAMEIP', 'localhost')
NAMING_SERVER_PORT = 8800
STORAGE_SERVER_PORT = 8801
PING_SERVERS_SECONDS = 20

# Codes
CMD_WRITE_FILE = 1
CMD_READ_FILE = 2
CMD_COPY_FILE = 3
CMD_DELETE_FILE = 4
CMD_CREATE_EMPTY_FILE = 5
CMD_FILE_INFO = 6
CMD_OPEN_DIR = 7
CMD_READ_DIR = 8
CMD_MAKE_DIR = 9
CMD_DELETE_DIR = 10
CMD_INIT = 11
CMD_FILE_MOVE = 12
CMD_CHECK_DIR = 13
CMD_GET_STORAGE = 14
CMD_CONFIRM_FILE_UPLOAD = 15
CMD_REPLICATE_FILE = 16
CMD_PING_FROM_STORAGE = 17
CMD_PING_FROM_NAMING = 18

ERR_FILE_NOT_EXIST = 100
ERR_FILE_DIR_NOT_EXIST = 101
ERR_DIR_NOT_EXIST = 102

CODE_OK = 200
CODE_FILE_NOT_EXIST = 201
CODE_FILE_ALREADY_EXIST = 202
CODE_DIRECTORY_NOT_EXIST = 203
CODE_DIRECTORY_ALREADY_EXIST = 204

DIR_OPEN_OK = 301
DIR_OPEN_NOT_EXIST = 302
DIR_OPEN_PREV = 303
DIR_OPEN_ROOT = 304

DIR_DELETE_NOT_EXIST = 307
DIR_DELETE_HAS_FILES = 308
DIR_DELETE_OK = 309

# yep
FILE_RECEIVE_CONFIRMATION_TO_NAMING = 1002
FILE_NOT_EXIST_ON_STORAGE_SERVER = 1003
FILE_EXISTS_ON_STORAGE_SERVER = 1004
CMD_FILE_CREATE = 1005
FILE_EXISTS = 1007
ERR_FILE_EXISTS = 1008
ERR_DIR_EXISTS = 1009
NOT_FORCE = 1010