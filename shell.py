from fs import FileSystem
import argparse


def load_fs_parser(command):
    parser = argparse.ArgumentParser(description="Load File System")
    parser.add_argument("--idx", type=str, help="Input value", required=True)
    parser.add_argument("--dir", type=str, help="Output value", required=True)
    parser.add_argument("--key", type=str,default=None, help="Output value", required=False)
    args = parser.parse_args(command.split())
    return args


class FileSystemShell:
    def __init__(self):
        self.filesystem = None
        self.status = 0
        self.prefix = None

    def start(self):
        print("use help command to check all commands")
        while self.status != 2:
            while self.status == 0:
                command = input(">>> ")
                if command.startswith("exit"):
                    self.status = 2
                else:
                    args = load_fs_parser(command)
                    if args.key:
                        key = bytes(args.key, encoding="utf-8")
                    else:
                        key = None
                    self.filesystem = FileSystem(index_file=args.idx, index_dir=args.dir, key=key)
                    self.prefix = f"[{args.idx}@{args.dir}]"
                    self.status = 1
            while self.status == 1:
                command = input(f"{self.prefix}>>> ")
                command = command.strip().split(" ")
                if command[0] == "exit":
                    self.status = 0
                elif command[0] == "ls":
                    print(self.filesystem.ls())
                elif command[0] == "cd":
                    path = command[1] if len(command) > 1 else None
                    if not path:
                        print(f"Error: Missing directory path")
                        continue
                    self.filesystem.cd(path)
                elif command[0] == "pwd":
                    print(self.filesystem.pwd())
                elif command[0] == "sync":
                    path = command[1] if len(command) > 1 else None
                    if not path:
                        print(f"Error: Missing target path")
                        continue
                    self.filesystem.sync(path)
                elif command[0] == "recover":
                    source_dir = command[1] if len(command) > 1 else None
                    target_dir = command[2] if len(command) > 2 else None
                    if not source_dir or not target_dir:
                        print(f"Error: Missing source or target path")
                        continue
                    self.filesystem.recover(source_dir, target_dir)
                else:
                    print(f"Command {command[0]} not recognized")


if __name__ == "__main__":
    shell = FileSystemShell()
    shell.start()