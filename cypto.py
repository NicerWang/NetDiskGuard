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

    def encrypt_file(self, old_hash, source_file_path, target_file_path):
        with open(source_file_path, 'rb') as f:
            file_data = f.read()
            encrypted_data = self.client.encrypt(file_data)
            hash = self.sha256(file_data)
        if hash == old_hash:
            return hash
        with open(target_file_path + "/" + hash, 'wb') as f:
            f.write(encrypted_data)
        return hash

    def dencrypt_file(self, source_file_path, target_file_path):
        with open(source_file_path, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = self.client.decrypt(encrypted_data)
        with open(target_file_path, 'wb') as f:
            f.write(decrypted_data)
