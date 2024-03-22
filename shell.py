from fs import FileSystem
import argparse


def load_fs_parser(command):
    parser = argparse.ArgumentParser(prog="", description="加载文件系统", add_help=False)
    parser.add_argument("-i", "--idx", type=str, help="索引文件位置", required=True)
    parser.add_argument("-d", "--dir", type=str, help="实际文件目录", required=False)
    parser.add_argument("-k", "--key", type=str, default=None, help="索引加密密钥", required=False)
    args = parser.parse_args(command.split()[1:])
    return args

class FileSystemShell:
    def __init__(self):
        self.filesystem = None
        self.status = 0
        self.prefix = None

    def start(self):
        while self.status != 2:
            print("使用方法: load -i 索引文件位置 [-d 实际文件目录] [-k 索引加密密钥]\n"
                  "         exit - 退出")
            while self.status == 0:
                command = input(">>> ")
                if command.startswith("exit"):
                    self.status = 2
                elif command.startswith("load"):
                    args = load_fs_parser(command)
                    if args.key:
                        key = bytes(args.key, encoding="utf-8")
                    else:
                        key = None
                    self.filesystem = FileSystem(index_file=args.idx, index_dir=args.dir, key=key)
                    self.prefix = f"[{args.idx}@{args.dir}]"
                    self.status = 1
                else:
                    print(f"[错误]命令`{command.split()[0]}`不存在")
            print("使用方法: ls - 查看当前路径下的所有文件\n"
                  "         pwd - 查看当前路径\n"
                  "         cd 目标路径 - 切换目录\n"
                  "         cat 当前目录下的文件名 - 查看实际文件对应的加密文件名\n"   
                  "         sync 加密文件存储目录 - 加密文件并更新索引\n"
                  "         recover 加密文件目录 恢复目标目录 - 恢复加密文件\n"   
                  "         exit - 退出")
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
                        print(f"[错误]缺少目标路径，命令格式: `cd 目标路径`.")
                        continue
                    try:
                        self.filesystem.cd(path)
                    except Exception as e:
                        print("[错误]cd失败，原因是:")
                        print(e)
                elif command[0] == "pwd":
                    print(self.filesystem.pwd())
                elif command[0] == "cat":
                    file = command[1] if len(command) > 1 else None
                    if not file:
                        print(f"[错误]缺少当前目录下的文件名，命令格式: `cat 当前目录下的文件名`.")
                        continue
                    try:
                        hash = self.filesystem.cat(file)
                        print(f"对应文件名为:`{hash}`.")
                    except Exception as e:
                        print("[错误]cat失败，原因是:")
                        print(e)
                elif command[0] == "sync":
                    path = command[1] if len(command) > 1 else None
                    if not path:
                        print(f"[错误]缺少加密文件存储目录，命令格式: `sync 加密文件存储目录`.")
                        continue
                    try:
                        self.filesystem.sync(path)
                    except Exception as e:
                        print("[错误]sync失败，原因是:")
                        print(e)
                elif command[0] == "recover":
                    source_dir = command[1] if len(command) > 1 else None
                    target_dir = command[2] if len(command) > 2 else None
                    if not source_dir or not target_dir:
                        print(f"[错误]缺少目录信息，命令格式: `recover 加密文件目录 恢复目标目录`.")
                        continue
                    try:
                        self.filesystem.recover(source_dir, target_dir)
                    except Exception as e:
                        print("[错误]recover失败，原因是:")
                        print(e)
                else:
                    print(f"[错误]命令`{command[0]}`不存在")


if __name__ == "__main__":
    shell = FileSystemShell()
    shell.start()