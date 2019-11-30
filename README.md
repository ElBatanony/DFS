# Distributed File System

Usage:

1. Go to repository root directory
2. Open terminal in this directory and run **python run super_client.py**
3. Place files to upload in client_files folder

Use following commands to work with DFS:

_(all file names should be related to **client_files** folder)_

- ***init*** initializes the server, discards all changes
- ***touch <file_name>*** creates an empty file
- ***w <file_name>*** uploads the file from **client_files** folder to the server
- ***r <file_name>*** reads the file from the server to **client_files** folder
- ***rm <file_name>*** removes the file
- ***info <file_name>*** gets information about the file from the server
- ***cp <source_file_name> <destination_file_name>*** creates copy of the file
- ***mv <source_path> <destination_path>*** moves a file from source path to destination path
- ***mv <source_path> <destination_path>*** moves a file from source path to destination path
- ***cd <new_directory>*** changes directory
- ***ls*** reads content of the directory
- ***mkdir <directory_name>*** creates new directory
- ***rmdir <directory_name> r(optional)*** remove directory _(r - remove recursively)_
- ***exit*** closes the client
