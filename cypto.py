import os.path

from cryptography.fernet import Fernet
import hashlib

class CipherSuite:
    def __init__(self, key=None, build=False):
        if build:
            self.key = Fernet.generate_key()
        else:
            self.key = key
        self.client = Fernet(self.key)

    def get_key(self):
        return self.key

    def sha256(self, bytes):
        readable_hash = hashlib.sha256(bytes).hexdigest()
        return readable_hash

    def encrypt_file(self, old_hashs, source_file_path, target_file_path):
        with open(source_file_path, 'rb') as f:
            file_data = f.read()
            hash = self.sha256(file_data + bytes(source_file_path, encoding="utf-8"))
            if hash in old_hashs:
                return hash
            encrypted_data = self.client.encrypt(file_data)
        with open(os.path.join(target_file_path, hash), 'wb') as f:
            f.write(encrypted_data)
        return hash

    def dencrypt_file(self, source_file_path, target_file_path):
        with open(source_file_path, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = self.client.decrypt(encrypted_data)
        with open(target_file_path, 'wb') as f:
            f.write(decrypted_data)

    def encrypt_str(self, string):
        data = bytes(string, encoding="utf-8")
        encrypted_data = self.client.encrypt(data)
        return encrypted_data

    def dencrypt_str(self, data):
        encrypted_data = self.client.decrypt(data)
        return str(encrypted_data, encoding="utf-8")

