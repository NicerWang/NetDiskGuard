import os
import logging
from datetime import datetime

from cypto import CipherSuite

TEST_STR = "Nicer"


class FileSystem:
    def __init__(self, index_file, index_dir, key=None):
        if os.path.exists(index_file):
            if key is None:
                raise Exception("索引文件存在，但未提供加密密钥.")

        self.index_file = index_file
        self.index_dir = index_dir
        if os.path.exists(index_file):
            logging.log(level=logging.INFO, msg="尝试读取索引文件中.")
            self.__from_index(index_file)
            logging.log(level=logging.INFO, msg="索引文件读取成功.")
        else:
            logging.log(level=logging.INFO, msg="在执行sync后，索引文件才会被创建.")
            self.root = {"name": "", "type": "directory", "children": {}, "parent": None}
            self.current_node = self.root
            self.hash_mapping = {}
            self.activate_hash = {}

        if not key:
            logging.log(level=logging.INFO, msg="首次创建索引文件，创建随机密钥中.")
            self.ciper = CipherSuite(build=True)
            key = self.ciper.get_key()
            self.test_ciper = self.ciper.encrypt_str(TEST_STR)
            logging.log(level=logging.INFO,
                        msg=f"该索引文件的密钥为(请牢记，丢失后将无法读取索引文件):{str(key, encoding='utf-8')}")
        else:
            try:
                self.ciper = CipherSuite(key=key)
                if self.ciper.dencrypt_str(self.test_ciper) != TEST_STR:
                    raise Exception("加密密钥错误.")
            except Exception:
                raise Exception("加密密钥错误.")

    def __load_file_change(self, init_dir, parent_node):
        for file_name in os.listdir(init_dir):
            file_path = os.path.join(init_dir, file_name)
            if os.path.isdir(file_path):
                dir_node = {"name": file_name, "type": "directory", "children": {}, "parent": parent_node}
                parent_node["children"][file_name] = dir_node
                self.__load_file_change(file_path, dir_node)
            else:
                parent_node["children"][file_name] = {"name": file_name, "type": "file", "fpath": file_path,
                                                      "parent": parent_node, "size": os.path.getsize(file_path),
                                                      "hash": None}

    def cd(self, path):
        split_path = path.split('/')
        if split_path[0] == '':
            current_node = self.root
            split_path = split_path[1:]
        else:
            current_node = self.current_node
        for directory in split_path:
            if directory == '..':
                if current_node["parent"] is not None:
                    current_node = current_node["parent"]
                else:
                    current_node = current_node
            elif directory not in current_node["children"] or current_node["children"][directory][
                "type"] != "directory":
                raise Exception(f"目录{directory}不存在.")
            else:
                current_node = current_node["children"][directory]
        self.current_node = current_node

    def ls(self):
        dirs = []
        files = []
        for name, node in self.current_node["children"].items():
            if node["type"] == "directory":
                dirs.append(name + '/')
            else:
                files.append(name)
        return dirs + files

    def pwd(self):
        node = self.current_node
        path = []
        while node != self.root:
            path.append(node["name"])
            node = node["parent"]
        path.append("ROOT")
        return "/".join(reversed(path))

    def cat(self, filename):
        if filename not in self.current_node["children"]:
            raise Exception(f"当前目录下，文件{filename}不存在.")
        hash = self.current_node["children"][filename]["hash"]
        if not hash:
            raise Exception(f"文件{filename}未经Sync操作处理.")
        return hash

    def sync(self, target_dir):
        if self.index_dir is None:
            raise Exception(f"Sync实际文件目录未指定，请执行exit后重新执行load，并指定-d参数.")
        logging.log(level=logging.INFO, msg="尝试Sync中.")
        target_dir = os.path.join(target_dir, str("_".join(str(datetime.now()).split())))
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        logging.log(level=logging.INFO, msg=f"[1/3]检测实际文件系统目录{self.index_dir}变动中.")
        self.root = {"name": "", "type": "directory", "children": {}, "parent": None}
        self.current_node = self.root
        self.__load_file_change(self.index_dir, self.root)
        logging.log(level=logging.INFO, msg="[2/3]更新索引并加密文件中.")
        self.activate_hash = {}
        self.__update_structure(self.root, target_dir)
        logging.log(level=logging.INFO, msg=f"[3/3]保存索引文件到{self.index_file}中.")
        self.__to_index()
        logging.log(level=logging.INFO, msg="保存完成.")

    def __update_structure(self, node, target_dir):
        for name, child in node["children"].items():
            if child["type"] == "file":
                hash = self.ciper.encrypt_file(self.hash_mapping.keys(), child["fpath"], target_dir)
                node["children"][name]["hash"] = hash
                self.hash_mapping[hash] = child
                self.activate_hash[hash] = child
            elif child["type"] == "directory":
                self.__update_structure(child, target_dir)

    def recover(self, source_dir, target_dir):
        logging.log(level=logging.INFO, msg=f"尝试解密{source_dir}中所有的加密文件.")
        for dir_path, dir_names, filenames in os.walk(source_dir):
            for filename in filenames:
                hash = filename
                if hash not in self.activate_hash.keys():
                    logging.log(level=logging.WARN, msg=f"文件`{hash}`已失效.")
                    continue
                target_path = self.hash_mapping[hash]["fpath"]
                file_path = os.path.join(target_dir, target_path)
                folder_path = os.path.dirname(file_path)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                self.ciper.dencrypt_file(os.path.join(dir_path, filename), file_path)
        logging.log(level=logging.INFO, msg=f"解密成功，解密后的文件存储在{target_dir}.")

    def clear(self, path):
        if not path:
            path = "invalid_" + str("_".join(str(datetime.now()).split())) + ".txt"
        logging.log(level=logging.INFO, msg=f"正在检测失效文件，此过程在上次Sync的结果上进行.")
        invalids = []
        for key in self.hash_mapping.keys():
            if key not in self.activate_hash:
                invalids.append(key)
        for key in invalids:
            self.hash_mapping.pop(key)
        if len(invalids) == 0:
            logging.log(level=logging.INFO, msg=f"无失效文件.")
            return
        logging.log(level=logging.INFO, msg=f"检测到{len(invalids)}个失效文件.")
        with open(path, "w+") as f:
            for key in invalids:
                f.write(key)
                f.write("\n")
        logging.log(level=logging.INFO, msg=f"失效文件列表已写入{path}.")
        self.__to_index()
        logging.log(level=logging.INFO, msg=f"已保存索引文件到{self.index_file}.")

    def __to_index(self):
        import pickle
        index = {
            "root": self.root,
            "current_node": self.current_node,
            "hash_mapping": self.hash_mapping,
            "activate_hash": self.activate_hash,
            "test_ciper": self.test_ciper
        }
        with open(self.index_file, "wb") as f:
            pickle.dump(index, f)

    def __from_index(self, index_file):
        import pickle
        with open(index_file, "rb") as f:
            index = pickle.load(f)
        self.root = index["root"]
        self.current_node = index["current_node"]
        self.hash_mapping = index["hash_mapping"]
        self.activate_hash = index["activate_hash"]
        self.test_ciper = index["test_ciper"]
