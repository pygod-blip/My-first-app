from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import json
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(50), nullable=False)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    table_number = db.Column(db.Integer, nullable=False)
    items = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if not (username and password and role):
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('add_user'))

        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        new_user = User(username=username, password_hash=password_hash, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('User added successfully.', 'success')
        return redirect(url_for('index'))

    return render_template('add_user.html')

@app.route('/authenticate_user', methods=['GET', 'POST'])
def authenticate_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not (username and password):
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('authenticate_user'))

        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        user = User.query.filter_by(username=username, password_hash=password_hash).first()

        if user:
            flash(f'Welcome, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('authenticate_user'))

    return render_template('authenticate_user.html')

# Similar routes can be added for menu management (add_menu_item, view_menu), and order management (place_order, view_orders).

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)