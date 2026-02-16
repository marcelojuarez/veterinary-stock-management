from db.database import db

class CompanyModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or db 

    def add_company_data(self, data):
        try:
            query = """
            INSERT INTO company (business_name, cuit, iva_condition, start_date, address, 
            city, province, postal_code, phone1, phone2) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params =  [
                data['business_name'],
                data['cuit'],
                data['iva_condition'],
                data['start_date'], 
                data['address'],
                data['city'],
                data['province'],
                data['postal_code'],
                data['phone1'],
                data['phone2'],
            ]

            return self.db.execute_query(query, params)
        except ValueError as e:
            print(f'Error al cargar datos de la empresa: {e}')

    def get_company_data(self):
        try:
            query = """
            SELECT * FROM company WHERE id = ?
            """
            params = [
                1,
            ]

            return self.db.fetch_one(query, params)

        except ValueError as e:
            print(f'Error al obtener los datos de la empresa: {e}')
            return None

    def edit_company_data(self, data):
        pass