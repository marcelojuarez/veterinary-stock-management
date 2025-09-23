from models.user import User
from models.security import validate_password


def validate_data(username, password):
    user_model = User()
    user = user_model.get_user_by_username(username)
    print(f'{user}')
    
    if not user:
        return False 
    
    hash_pwd = user[1]
    
    try:
        result = validate_password(hash_pwd, password)
        print(f'{result}')
        return result
    except:
        return False
