from gmssl import sm4


def encrypt(key, data):
    sm4_crypt = sm4.CryptSM4()
    sm4_crypt.set_key(key, sm4.SM4_ENCRYPT)
    encrypted_data = sm4_crypt.crypt_ecb(data)
    return encrypted_data


def decrypt(key, encrypted_data):
    sm4_crypt = sm4.CryptSM4()
    sm4_crypt.set_key(key, sm4.SM4_DECRYPT)
    decrypted_data = sm4_crypt.crypt_ecb(encrypted_data)
    return decrypted_data
