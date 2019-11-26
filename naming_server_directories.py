from logs import logger
from status_codes import CODE_DIRECTORY_NOT_EXIST, CODE_OK, CODE_DIRECTORY_ALREADY_EXIST, DIR_MAKE_OK, \
    DIR_DELETE_HAS_FILES, DIR_DELETE_OK, DIR_DELETE_NOT_EXIST

directories = {}


class Directory:
    def __init__(self, path):
        self.path = path
        self.directories = []
        self.files = {}


def get_prev(path): return '/'.join(path.split('/')[:-1])


def get_last(path): return path.split('/')[-1]


def reset_directories():
    global directories
    directories = {'': Directory('')}


def check_directory(directory_path):
    logger.info('checking dir ' + directory_path)
    if directory_path in directories:
        return CODE_OK
    else:
        return CODE_DIRECTORY_NOT_EXIST


def read_directory(directory_path):
    if directory_path in directories:
        ret = ' '
        for d in directories[directory_path].directories:
            ret += d + '/ '
        for file in directories[directory_path].files.keys():
            ret += file + ' '
        return ret
    else:
        return CODE_DIRECTORY_NOT_EXIST


def make_directory(directory_path):
    logger.info('make dir ' + directory_path)
    if directory_path in directories:
        return CODE_DIRECTORY_ALREADY_EXIST
    directories[directory_path] = Directory(directory_path)
    directory_name = get_last(directory_path)
    directories[get_prev(directory_path)].directories.append(directory_name)
    return DIR_MAKE_OK


def delete_directory(directory_path, force):
    logger.info('del dir ' + directory_path)
    if directory_path in directories:
        dir_files = directories[directory_path].files
        dir_dir = directories[directory_path].directories

        if not force:
            if dir_files or dir_dir:
                return DIR_DELETE_HAS_FILES

        for _ in dir_files:
            logger.info('no delete function defined')
            # delete_file(directory_path + '/' + file)
        for d in dir_dir:
            delete_directory(directory_path + '/' + d, True)

        directory_name = directory_path.split('/')[-1]

        # if get_prev(directory_path) != '':
        if directory_name in directories[get_prev(directory_path)].directories:
            directories[get_prev(directory_path)].directories.remove(
                directory_name)
        del directories[directory_path]

        return DIR_DELETE_OK
    else:
        return DIR_DELETE_NOT_EXIST
