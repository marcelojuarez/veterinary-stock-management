from views.main_view import App
from db.database import db

def main():
    try:
        print("establishing connection to the database")
        db.create_tables()
        print("database initialized")

        print("initializing app")
        app = App()
        print("app initialized")

        app.run()
        
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
    
if __name__ == '__main__':
    main()

