from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, abort
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
api = Api(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
# IMPORTANT! Always import models after initializing db instance otherwise circular import error will occur
from models import User, Expense, Category

# For proper serialization of data using marshmallow schema
class ExpenseSchema(ma.Schema):
    class Meta:
        fields = ("id", "expense_name", "amount", "note",
                  "expense_date", "category_id")
        model = Expense


# For one record
expense_schema = ExpenseSchema()
# For a list of records
expenses_schema = ExpenseSchema(many=True)

class ExpensesList(Resource):
    '''
        This resource is used for creating and retreiving user expenses
    '''

    def get(self, user_id):
        '''
            This get method takes in a User id and returns all it's expenses from the database
        '''
        user_expenses = Expense.query.filter_by(user_id=user_id).all()
        # serialize the expense data
        return expenses_schema.dump(user_expenses)

    def post(self, user_id):
        '''
            This method takes in a User id and creates an expense against it
        '''
        parsed_date = datetime.strptime(request.json['expense_date'], "%Y-%m-%d").date()
        new_expense = Expense(
            expense_name=request.json['expense_name'],
            amount=request.json['amount'],
            note=request.json['note'],
            expense_date=parsed_date,
            user_id=request.json['user_id'],
            category_id=request.json['category_id']
        )

        db.session.add(new_expense)
        db.session.commit()
        return expense_schema.dump(new_expense), 201

class Expenses(Resource):
    '''
        This resource is used for updating and deleting expenses for a specific user
    '''
    def get(self, expense_id):
        '''
            This method takes in an Expense id and returns it's data
        '''
        expense_single = Expense.query.get_or_404(expense_id)
        return expense_schema.dump(expense_single)

    def put(self, expense_id):
        '''
            This method takes in an Expense id and updates it
        '''
        expense = Expense.query.get_or_404(expense_id)
        
        expense.expense_name = request.json['expense_name']
        expense.amount = request.json['amount']
        expense.note = request.json['note']
        parsed_date = datetime.strptime(request.json['expense_date'], "%Y-%m-%d").date()
        expense.expense_date = parsed_date
        expense.category_id = request.json['category_id']

        db.session.commit()
        return expense_schema.dump(expense), 201



    def delete(self, expense_id):
        '''
            This method takes in an Expense id and deletes it
        '''
        expense = Expense.query.get_or_404(expense_id)
        db.session.delete(expense)
        db.session.commit()
        return 'Delete Successful', 204

# for serialization of Categories data
class CategoriesSchema(ma.Schema):
    class Meta:
        fields = ("id", "category_name")
        model = Category

categories_schema = CategoriesSchema(many=True)

class CategoriesList(Resource):
    def get(self):
        categories = Category.query.all()
        return categories_schema.dump(categories)

# for serialization of Users data
class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username")
        model = User

user_schema = UserSchema()

def email_exists(email):
        user = User.query.filter_by(email=email).first()
        return user

class Authentication(Resource):
    '''
        This resource is for the purpose of authentication of users
    '''
    def get(self):
        email = request.json['email']
        password = request.json['password']

        # First check if the email is registered
        user = User.query.filter_by(email=email).first()
        # If the user exists and password is valid then log them in
        if user and bcrypt.check_password_hash(user.password, password):
            return user_schema.dump(user)
        else:
            abort(401, error_message="Invalid email or password")


    def post(self):
        # Check if the email already exists, if it does return forbidden error code else save user data.
        if email_exists(request.json['email']):
            abort(403, error_message=f"User with email {request.json['email']} already exists!")
        else:
            user = User(
                username=request.json['username'],
                email=request.json['email']
            )
            user.hash_password(request.json['password'])
            db.session.add(user)
            db.session.commit()

            return user_schema.dump(user), 201


api.add_resource(ExpensesList, '/expenses/<user_id>')
api.add_resource(Expenses, '/expense/<expense_id>')
api.add_resource(CategoriesList, '/categories')
api.add_resource(Authentication, '/authenticate')