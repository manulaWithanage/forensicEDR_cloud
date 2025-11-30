from Crypto.Cipher import AES
import os

key = os.urandom(32)
cipher = AES.new(key, AES.MODE_GCM)
print(f"Nonce length: {len(cipher.nonce)}")
