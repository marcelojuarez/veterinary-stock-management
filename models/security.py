from argon2 import PasswordHasher

ph = PasswordHasher()

def gen_password(password):
    # genera el hash de la contraseña
    return ph.hash(password)

def validate_password(hash_pwd, pwd):
    # verifica la contraseña ingresada con el hash
    try:
        ph.verify(hash_pwd, pwd)
        return True
    except:
        return False


