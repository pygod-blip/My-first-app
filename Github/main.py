import tkinter as tk
from tkinter import messagebox, ttk
import random
from datetime import datetime
import json
import sqlite3
import hashlib
import logging
from collections import defaultdict 
import sys  

# Set up logging configuration
logging.basicConfig(filename='restaurant.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class User:
    def __init__(self, username, password_hash, role):
        self.username = username
        self.password_hash = password_hash
        self.role = role

class UserManager:
    def __init__(self, db_filename='restaurant.db'):
        self.conn = sqlite3.connect(db_filename)
        self.create_users_table()

    def create_users_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    role TEXT
                )
            ''')

    def add_user(self, username, password, role):
        password_hash = self.hash_password(password)
        with self.conn:
            self.conn.execute('''
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            ''', (username, password_hash, role))
        logging.info(f"Added user: {username}, Role: {role}")

    def authenticate(self, username, password):
        password_hash = self.hash_password(password)
        cursor = self.conn.execute('''
            SELECT * FROM users
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        user_data = cursor.fetchone()
        if user_data:
            logging.info(f"User authenticated: {username}")
            return User(user_data[1], user_data[2], user_data[3])
        logging.warning(f"Failed authentication attempt for user: {username}")
        return None

    def hash_password(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

class MenuItem:
    def __init__(self, name, description, price, category):
        self.id = random.randint(1, 1000)  # Random ID for each menu item
        self.name = name
        self.description = description
        self.price = price
        self.category = category

class MenuManager:
    def __init__(self, db_filename='restaurant.db'):
        self.conn = sqlite3.connect(db_filename)
        self.create_menu_items_table()
        self.menu_items_by_category = defaultdict(list) 

    def create_menu_items_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    price REAL,
                    category TEXT
                )
            ''')

    def add_menu_item(self, name, description, price, category):
        with self.conn:
            self.conn.execute('''
                INSERT INTO menu_items (name, description, price, category)
                VALUES (?, ?, ?, ?)
            ''', (name, description, price, category))
        logging.info(f"Added menu item: {name}, Category: {category}")
        self.menu_items_by_category[category].append(MenuItem(name, description, price, category))

    def get_menu_items_by_category(self, category):
        return self.menu_items_by_category.get(category, [])

    def get_menu_items(self):
        cursor = self.conn.execute('SELECT * FROM menu_items')
        menu_items = []
        for row in cursor:
            menu_item = MenuItem(row[1], row[2], row[3], row[4])
            menu_item.id = row[0]
            menu_items.append(menu_item)
            self.menu_items_by_category[row[4]].append(menu_item) 
        return menu_items

class Order:
    def __init__(self, order_id, table_number, items):
        self.id = random.randint(1, 1000) 
        self.order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.table_number = table_number
        self.items = items
        self.status = "Pending"

class OrderManager:
    def __init__(self, db_filename='restaurant.db'):
        self.conn = sqlite3.connect(db_filename)
        self.create_orders_table()

    def create_orders_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_time TEXT,
                    table_number INTEGER,
                    items TEXT,
                    status TEXT
                )
            ''')

    def place_order(self, table_number, items):
        items_json = json.dumps([vars(item) for item in items])
        with self.conn:
            self.conn.execute('''
                INSERT INTO orders (order_time, table_number, items, status)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), table_number, items_json, "Pending"))
        logging.info(f"Placed order for table {table_number}")

    def view_orders(self):
        cursor = self.conn.execute('SELECT * FROM orders')
        orders = []
        for row in cursor:
            order_items = [MenuItem(item['name'], item['description'], item['price'], item['category']) for item in json.loads(row[3])]
            order = Order(row[0], row[2], order_items)
            order.order_time = row[1]
            order.status = row[4]
            orders.append(order)
        return orders

class RestaurantManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Restaurant Management System")
        self.db_filename = self.get_db_filename()  
        self.user_manager = UserManager(self.db_filename)
        self.menu_manager = MenuManager(self.db_filename)
        self.order_manager = OrderManager(self.db_filename)
        self.create_main_menu()

    def get_db_filename(self):
        if len(sys.argv) > 1:
            return sys.argv[1]
        else:
            return 'restaurant.db' 

    def create_main_menu(self):
        self.main_menu = tk.Menu(self.root)
        self.root.config(menu=self.main_menu)

        self.user_menu = tk.Menu(self.main_menu, tearoff=False)
        self.main_menu.add_cascade(label="Users", menu=self.user_menu)
        self.user_menu.add_command(label="Add User", command=self.add_user_window)
        self.user_menu.add_command(label="Authenticate User", command=self.authenticate_user_window)

        self.menu_item_menu = tk.Menu(self.main_menu, tearoff=False)
        self.main_menu.add_cascade(label="Menu Items", menu=self.menu_item_menu)
        self.menu_item_menu.add_command(label="Add Menu Item", command=self.add_menu_item_window)
        self.menu_item_menu.add_command(label="View Menu", command=self.view_menu_window)

        self.order_menu = tk.Menu(self.main_menu, tearoff=False)
        self.main_menu.add_cascade(label="Orders", menu=self.order_menu)
        self.order_menu.add_command(label="Place Order", command=self.place_order_window)
        self.order_menu.add_command(label="View Orders", command=self.view_orders_window)

    def add_user_window(self):
        self.user_window = tk.Toplevel(self.root)
        self.user_window.title("Add User")
        self.user_window.configure(bg='#f0f0f0')  # Light gray background

        tk.Label(self.user_window, text="Username:", bg='#f0f0f0', fg='blue').grid(row=0, column=0, padx=10, pady=5)
        self.username_entry = tk.Entry(self.user_window)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.user_window, text="Password:", bg='#f0f0f0', fg='blue').grid(row=1, column=0, padx=10, pady=5)
        self.password_entry = tk.Entry(self.user_window, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.user_window, text="Role:", bg='#f0f0f0', fg='blue').grid(row=2, column=0, padx=10, pady=5)
        self.role_entry = tk.Entry(self.user_window)
        self.role_entry.grid(row=2, column=1, padx=10, pady=5)

        add_button = tk.Button(self.user_window, text="Add User", bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'), command=self.add_user)
        add_button.grid(row=3, columnspan=2, padx=10, pady=10)

    def add_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = self.role_entry.get()

        if username and password and role:
            self.user_manager.add_user(username, password, role)
            messagebox.showinfo("Success", "User added successfully.")
            self.user_window.destroy()
        else:
            messagebox.showerror("Error", "Please fill in all fields.")

    def authenticate_user_window(self):
        self.auth_window = tk.Toplevel(self.root)
        self.auth_window.title("Authenticate User")
        self.auth_window.configure(bg='#f0f0f0')  # Light gray background

        tk.Label(self.auth_window, text="Username:", bg='#f0f0f0', fg='blue').grid(row=0, column=0, padx=10, pady=5)
        self.auth_username_entry = tk.Entry(self.auth_window)
        self.auth_username_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.auth_window, text="Password:", bg='#f0f0f0', fg='blue').grid(row=1, column=0, padx=10, pady=5)
        self.auth_password_entry = tk.Entry(self.auth_window, show="*")
        self.auth_password_entry.grid(row=1, column=1, padx=10, pady=5)

        authenticate_button = tk.Button(self.auth_window, text="Authenticate", bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'), command=self.authenticate_user)
        authenticate_button.grid(row=2, columnspan=2, padx=10, pady=10)

    def authenticate_user(self):
        username = self.auth_username_entry.get()
        password = self.auth_password_entry.get()

        if username and password:
            user = self.user_manager.authenticate(username, password)
            if user:
                messagebox.showinfo("Authentication Successful", f"Welcome, {username}!")
                self.auth_window.destroy()
            else:
                messagebox.showerror("Authentication Failed", "Invalid username or password.")
        else:
            messagebox.showerror("Error", "Please fill in all fields.")

    def add_menu_item_window(self):
        self.menu_item_window = tk.Toplevel(self.root)
        self.menu_item_window.title("Add Menu Item")
        self.menu_item_window.configure(bg='#f0f0f0')  # Light gray background

        tk.Label(self.menu_item_window, text="Name:", bg='#f0f0f0', fg='blue').grid(row=0, column=0, padx=10, pady=5)
        self.menu_item_name_entry = tk.Entry(self.menu_item_window)
        self.menu_item_name_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.menu_item_window, text="Description:", bg='#f0f0f0', fg='blue').grid(row=1, column=0, padx=10, pady=5)
        self.menu_item_desc_entry = tk.Entry(self.menu_item_window)
        self.menu_item_desc_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.menu_item_window, text="Price:", bg='#f0f0f0', fg='blue').grid(row=2, column=0, padx=10, pady=5)
        self.menu_item_price_entry = tk.Entry(self.menu_item_window)
        self.menu_item_price_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(self.menu_item_window, text="Category:", bg='#f0f0f0', fg='blue').grid(row=3, column=0, padx=10, pady=5)
        self.menu_item_category_entry = tk.Entry(self.menu_item_window)
        self.menu_item_category_entry.grid(row=3, column=1, padx=10, pady=5)

        add_button = tk.Button(self.menu_item_window, text="Add Menu Item", bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'), command=self.add_menu_item)
        add_button.grid(row=4, columnspan=2, padx=10, pady=10)

    def add_menu_item(self):
        name = self.menu_item_name_entry.get()
        description = self.menu_item_desc_entry.get()
        price = float(self.menu_item_price_entry.get())
        category = self.menu_item_category_entry.get()

        if name and description and price and category:
            self.menu_manager.add_menu_item(name, description, price, category)
            messagebox.showinfo("Success", "Menu item added successfully.")
            self.menu_item_window.destroy()
        else:
            messagebox.showerror("Error", "Please fill in all fields.")

    def view_menu_window(self):
        self.view_menu_window = tk.Toplevel(self.root)
        self.view_menu_window.title("View Menu")
        self.view_menu_window.configure(bg='#f0f0f0')  # Light gray background

        menu_items = self.menu_manager.get_menu_items()

        for i, menu_item in enumerate(menu_items):
            tk.Label(self.view_menu_window, text=f"{menu_item.name} - {menu_item.price}", bg='#f0f0f0').grid(row=i, column=0, padx=10, pady=5)

    def place_order_window(self):
        self.place_order_window = tk.Toplevel(self.root)
        self.place_order_window.title("Place Order")
        self.place_order_window.configure(bg='#f0f0f0')  # Light gray background

        self.table_number_label = tk.Label(self.place_order_window, text="Table Number:", bg='#f0f0f0', fg='blue')
        self.table_number_label.grid(row=0, column=0, padx=10, pady=5)
        self.table_number_entry = tk.Entry(self.place_order_window)
        self.table_number_entry.grid(row=0, column=1, padx=10, pady=5)

        self.menu_items = self.menu_manager.get_menu_items()

        self.menu_items_checkbuttons = []
        for i, menu_item in enumerate(self.menu_items):
            var = tk.IntVar()
            checkbutton = tk.Checkbutton(self.place_order_window, text=f"{menu_item.name} - {menu_item.price}", variable=var, bg='#f0f0f0')
            checkbutton.grid(row=i + 1, column=0, padx=10, pady=5)
            self.menu_items_checkbuttons.append((var, menu_item))

        place_order_button = tk.Button(self.place_order_window, text="Place Order", bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'), command=self.place_order)
        place_order_button.grid(row=len(self.menu_items) + 1, columnspan=2, padx=10, pady=10)

    def place_order(self):
        table_number = self.table_number_entry.get()
        selected_items = [item[1] for item in self.menu_items_checkbuttons if item[0].get() == 1]

        if table_number and selected_items:
            self.order_manager.place_order(table_number, selected_items)
            messagebox.showinfo("Success", "Order placed successfully.")
            self.place_order_window.destroy()
        else:
            messagebox.showerror("Error", "Please select items and enter a table number.")

    def view_orders_window(self):
        self.view_orders_window = tk.Toplevel(self.root)
        self.view_orders_window.title("View Orders")
        self.view_orders_window.configure(bg='#f0f0f0')  # Light gray background

        orders = self.order_manager.view_orders()

        for i, order in enumerate(orders):
            tk.Label(self.view_orders_window, text=f"Order ID: {order.id}, Table: {order.table_number}, Time: {order.order_time}, Status: {order.status}", bg='#f0f0f0').grid(row=i, column=0, padx=10, pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = RestaurantManagementApp(root)
    root.mainloop()

