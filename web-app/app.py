from flask import Flask, request, render_template, redirect, jsonify, flash, session
from flask.config import ConfigAttribute
from flask.helpers import url_for
import requests
from functools import wraps
import json

import base64
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

app = Flask(__name__)

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login first!', 'danger')
            return redirect(url_for('sign_in'))
    return wrap
@app.route('/sign-in')
@app.route('/', methods=['GET', 'POST'])
def sign_in():
    if request.method == "POST":
        user_data = {
            "email": request.form['email'],
            "password": request.form['password']
        }

        response = requests.get("http://127.0.0.1:5000/authenticate", json=user_data)
        # Status code 201 means successfully created
        if response.status_code == 200:
            session['logged_in'] = True
            session['user_id'] = response.json()['id']
            session['username'] = response.json()['username']
            return jsonify({'success': 'Login successful! Redirecting...'})
        elif response.status_code == 401: # 401 means unauthorized
            return jsonify({'error': response.json()['error_message']})
    return render_template('sign-in.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":

        user_data = {
            "username": request.form['username'],
            "email": request.form['email'],
            "password": request.form['password']
        }

        response = requests.post("http://127.0.0.1:5000/authenticate", json=user_data)
        # Status code 201 means successfully created
        if response.status_code == 201:
            return jsonify({'success': 'Registration Successful. You can now Log in'})
        elif response.status_code == 403: # 403 means forbidden
            return jsonify({'error': response.json()['error_message']})
        
    return render_template('register.html')

@app.route('/sign-out', methods=['POST'])
@is_logged_in
def sign_out():
    if request.method == "POST":
        # clear all the session variables
        session.clear()
        return redirect(url_for('sign_in'))

@app.route('/dashboard')
@is_logged_in
def index():
    # Send a get request to retrieve categories
    categories_response = requests.get("http://127.0.0.1:5000/categories")
    # Get the JSON data
    categories = categories_response.json()
    user_id = session['user_id']

    # Send a get request to retrieve all expenses for a user
    expenses_response = requests.get(f"http://127.0.0.1:5000/expenses/{user_id}")
    # Get the JSON data
    expenses = expenses_response.json()

    plot = create_pie_plot(categories, expenses)

    return render_template('index.html', categories=categories, expenses=expenses, plot=plot)


@app.route('/create', methods=['POST'])
@is_logged_in
def create():
    user_id = 1
    expense_data = {
            'expense_name': request.form['expense_name'],
            'amount': request.form['amount'],
            'expense_date': request.form['expense_date'],
            'note': request.form['note'],
            'category_id': request.form['category'],
            'user_id': session['user_id']
    }
    # POST the data to api for storing in the database
    response = requests.post(f"http://127.0.0.1:5000/expenses/{user_id}", json=expense_data)
    if response.status_code == 201:
        return jsonify({'success': 'New expense added successfully!'})
    else:
        return jsonify({'error': 'There was an error creating new expense.'})

@app.route('/delete', methods=["POST"])
@is_logged_in
def delete():
    if request.method == 'POST':
        delete_response = requests.delete(f"http://127.0.0.1:5000/expense/{request.form['expense_id']}")
        if delete_response.status_code == 204:
            flash('Expense deleted successfully', 'success')
        else:
            flash('There was an error performing the delete', 'danger')
        return redirect(url_for('index'))


@app.route('/update/<expense_id>', methods=['GET', 'POST'])
@is_logged_in
def update(expense_id):
    response = requests.get(f"http://127.0.0.1:5000/expense/{expense_id}")
    expense = response.json()

    # Send a get request to retrieve categories
    categories_response = requests.get("http://127.0.0.1:5000/categories")
    # Get the JSON data
    categories = categories_response.json()

    if request.method == "POST":
        expense_data = {
            'expense_name': request.form['expense_name'],
            'amount': request.form['amount'],
            'expense_date': request.form['expense_date'],
            'note': request.form['note'],
            'category_id': request.form['category'],
        }

        response = requests.put(f"http://127.0.0.1:5000/expense/{expense_id}", json=expense_data)
        
        if response.status_code == 201:
            return jsonify({'success': 'Expense Updated successfully!'})
        else:
            return jsonify({'error': 'There was an error performing the update'})

    return render_template('update.html', expense=expense, categories=categories)


def json_to_df(categories, expenses):
    for expense in expenses:
       expense['category'] = categories[expense['category_id']-1]['category_name']

    expenses_json = json.dumps(expenses)
    df = pd.read_json(expenses_json) # Convert json to dataframe
    return df.sort_values(by=['category_id'])
    

def create_pie_plot(categories, expenses):
    
    df = json_to_df(categories, expenses)
    # Generate the figure **without using pyplot**.
    fig,ax=plt.subplots(figsize=(6,6))
    ax=sns.set(style="darkgrid")
    #define data

    data = list(df.groupby('category_id').sum()['amount'].values) # Get the total amount per category
    labels = list(df.category.unique()) # Get categories
    print(data)
    print(labels)

    #define Seaborn color palette to use
    colors = sns.color_palette('husl')[0:5]

    #create pie chart
    plt.pie(data, labels = labels, colors = colors, autopct='%.0f%%')
    plt.title('Amount spent per category')
    canvas=FigureCanvas(fig)
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    src = f'data:image/png;base64,{data}'
    return src
    

if __name__ == '__main__':
    app.secret_key = '81d43f0a7f63babc337d0a529f91372f'
    app.run(debug=True, port=80)