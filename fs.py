import os

from cypto import CipherSuite


class FileSystem:
    def __init__(self, index_file, index_dir, key=None):
        if not key:
            self.ciper = CipherSuite(build=True)
            key = self.ciper.get_key()
            print(str(key, encoding="utf-8"))
        else:
            self.ciper = CipherSuite(key=key)

        self.index_file = index_file
        self.index_dir = index_dir
        if os.path.exists(index_file):
            self.__from_index(index_file)
        else:
            self.root = {"name": "", "type": "directory", "children": {}, "parent": None}
            self.current_node = self.root
            self.hash_mapping = {}
            self.missing_mapping = {}


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
                raise Exception(f"Directory {directory} does not exist")
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
            raise Exception(f"File {filename} not exists")
        hash = self.current_node["children"][filename]["hash"]
        if not hash:
            raise Exception(f"File {filename} not sync")
        return hash

    def sync(self, target_dir):
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        self.__load_file_change(self.index_dir, self.root)
        self.__update_structure(self.root, target_dir)
        self.__to_index()

    def __update_structure(self, node, target_dir):
        for name, child in node["children"].items():
            if child["type"] == "file":
                old_hash = child["hash"]
                hash = self.ciper.encrypt_file(old_hash, child["fpath"], target_dir)
                if old_hash != hash:
                    node["children"][name]["hash"] = hash
                    self.hash_mapping[hash] = child
                    if old_hash:
                        self.missing_mapping[old_hash] = self.hash_mapping[old_hash]["size"]
                        self.hash_mapping.pop(old_hash)
            elif child["type"] == "directory":
                self.__update_structure(child, target_dir)

    def recover(self, source_dir, target_dir):
        for dir_path, dir_names, filenames in os.walk(source_dir):
            for filename in filenames:
                hash = filename
                target_path = self.hash_mapping[hash]["fpath"]
                file_path = os.path.join(target_dir, target_path)
                folder_path = os.path.dirname(file_path)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                self.ciper.dencrypt_file(os.path.join(dir_path, filename), file_path)

    def __to_index(self):
        import pickle
        index = {
            "root": self.root,
            "current_node": self.current_node,
            "hash_mapping": self.hash_mapping,
            "missing_mapping": self.missing_mapping
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
        self.missing_mapping = index["missing_mapping"]


if __name__ == '__main__':
    # fs = FileSystem(index_dir="./test", index_file="index.idx")
    # fs.sync()

    fs = FileSystem(key=b"zEYMa_TU5L5isc_LInQe6DU4WoZFWv1Bq7dk6OH6KEw=", index_file="index.idx", index_dir="./test")
    print(fs.cat("1"))
    fs.recover("./netdiskguard", "./netdiskguard")

    # input() eV0k1N7efxn-d-DBuBmcymzh-iV8zSzVcaUbu_Y00j0=
