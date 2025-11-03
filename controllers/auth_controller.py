from models.user import User
from models.security import validate_password
from tkinter import messagebox


def validate_data(username, password):
    user_model = User()
    user = user_model.get_user_by_username(username)
    print(f'{user}')
    
    if not user:
        messagebox.showwarning('Error', 'Usuario no encontrado')
        return False 
    
    hash_pwd = user[1]
    
    if (validate_password(hash_pwd, password)):
        return True
    else:
        messagebox.showwarning('Error', 'Contraseña incorrecta')
        return False
