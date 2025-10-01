from db.database import db

class User():
    def __init__(self, db_connection=None):
        self.db = db_connection or db

    def add_new_user(self, user_data):
        query = "INSERT INTO usuarios values (?,?)"

        params = [
            user_data['username'],
            user_data['password']
        ]

        return self.db.execute_query(query, params)

    def get_user_by_username(self, username):
        try:
            query = "SELECT * FROM usuarios where username = ?"
            return self.db.fetch_one(query, (username,))
        except ValueError as e:
            print(f"Error getting user by username {e}")
            return None
        

