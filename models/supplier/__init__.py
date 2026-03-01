# models/supplier/__init__.py

from .supplier_core import SupplierCore
from .supplier_payment import SupplierPayment
from .supplier_purchase import SupplierPurchase
from db.database import db

class SupplierModel():
    def __init__(self, stock_model):
        self.db = db
        self.core = SupplierCore(db)
        self.purchase = SupplierPurchase(db, stock_model)
        self.payment = SupplierPayment(db, self.purchase)
