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
CMD_CLOSE_SOCK = 13
CMD_CHECK_DIR = 16
CMD_GET_STORAGE = 14
CMD_CONFIRM_FILE_UPLOAD = 15
CMD_REPLICATE_FILE = 16

ERR_FILE_NOT_EXIST = 100
ERR_FILE_DIR_NOT_EXIST = 101

CODE_OK = 200
CODE_FILE_NOT_EXIST = 201
CODE_FILE_ALREADY_EXIST = 202
CODE_DIRECTORY_NOT_EXIST = 203
CODE_DIRECTORY_ALREADY_EXIST = 204

DIR_OPEN_OK = 'Directory opened'
DIR_OPEN_NOT_EXIST = 'Directory to open does not exist'
DIR_OPEN_PREV = 'Directory changed to previous directory'
DIR_OPEN_ROOT = 'Already in root directory'

DIR_MAKE_EXISTS = 'Directory to create already exists'
DIR_MAKE_OK = 'Directory successfully created'

DIR_DELETE_NOT_EXIST = 'Directory to delete does not exist'
DIR_DELETE_HAS_FILES = 'Directory to delete has files or directories'
DIR_DELETE_OK = 'Directory successfully deleted'
