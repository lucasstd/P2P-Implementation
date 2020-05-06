from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome import Random
from base64 import b64encode, b64decode


class AESCipher:

    @staticmethod
    def create_key():
        return b64encode(os.urandom(AES.block_size)).decode()

    @staticmethod
    def is_aes_key(key):
        try:
            return len(b64decode(key.encode())) == AES.block_size
        except Exception as e:
            return False

    @staticmethod
    def encrypt(key, raw):
        assert type(raw) == bytes, "input data is bytes"
        if isinstance(key, str):
            key = b64decode(key.encode())
        raw = pad(raw, AES.block_size)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(raw)

    @staticmethod
    def decrypt(key, enc):
        assert type(enc) == bytes, 'Encrypt data is bytes'
        if isinstance(key, str):
            key = b64decode(key.encode())
        iv = enc[:AES.block_size]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        raw = cipher.decrypt(enc[AES.block_size:])
        raw = unpad(raw, AES.block_size)
        if len(raw) == 0:
            raise ValueError("AES decryption error, not correct key.")
        return raw