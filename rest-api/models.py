from api import db, bcrypt
from datetime import datetime
import json
from utils import defaultconverter

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    
    expenses = db.relationship('Expense', backref='user', lazy=True)

    def hash_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_name = db.Column(db.String(60))
    amount = db.Column(db.Integer, nullable=False)
    note = db.Column(db.Text)
    expense_date = db.Column(db.Date, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))



class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(20), unique=True, nullable=False)

    exps = db.relationship('Expense', uselist=False, backref='category')