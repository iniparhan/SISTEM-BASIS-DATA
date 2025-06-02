from flask import Flask, request, render_template, redirect, url_for, session
import pyodbc
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Konfigurasi koneksi ke SQL Server
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=LAPTOP-G4715JR0;"  # Ganti dengan nama server Anda
    "DATABASE=RBAC_Demo;"
    "Trusted_Connection=yes;"
)

# Fungsi untuk koneksi database
def get_db_connection():
    return pyodbc.connect(conn_str)

# Halaman login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Role FROM Users WHERE Username = ? AND Password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            session['role'] = user.Role
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# Halaman dashboard
@app.route('/dashboard?page=1')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['role'] != 'Admin':
        return "Access Denied: Admin only"
    
    page = request.args.get('page', 1, type=int)
    per_page = 100
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query dengan pagination
    start_time = time.time()
    cursor.execute("""
        SELECT SaleID, ProductName, SaleDate, Amount 
        FROM SalesData 
        ORDER BY SaleID 
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """, (offset, per_page))
    data = cursor.fetchall()
    
    # Hitung total data untuk pagination
    cursor.execute("SELECT COUNT(*) FROM SalesData")
    total_rows = cursor.fetchone()[0]
    total_pages = (total_rows // per_page) + (1 if total_rows % per_page > 0 else 0)
    
    conn.close()
    
    return render_template('dashboard.html', data=data, page=page, total_pages=total_pages, query_time=time.time() - start_time)

if __name__ == '__main__':
    app.run(debug=True)





# from flask import Flask, request, render_template, redirect, url_for, session
# import pyodbc
# import time

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'

# # Konfigurasi koneksi ke SQL Server
# conn_str = (
#     "DRIVER={ODBC Driver 17 for SQL Server};"
#     "SERVER=LAPTOP-G4715JR0;"  # Ganti dengan nama server Anda
#     "DATABASE=RBAC_Demo;"
#     "Trusted_Connection=yes;"
# )

# # Fungsi untuk koneksi database
# def get_db_connection():
#     return pyodbc.connect(conn_str)

# # Halaman login
# @app.route('/', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
        
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT Role FROM Users WHERE Username = ? AND Password = ?", (username, password))
#         user = cursor.fetchone()
#         conn.close()
        
#         if user:
#             session['username'] = username
#             session['role'] = user.Role
#             return redirect(url_for('dashboard'))
#         else:
#             return render_template('login.html', error="Invalid credentials")
#     return render_template('login.html')

# # Halaman dashboard (tanpa pagination untuk testing)
# @app.route('/dashboard')
# def dashboard():
#     if 'username' not in session:
#         return redirect(url_for('login'))
    
#     if session['role'] != 'Admin':
#         return "Access Denied: Admin only"
    
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     # Query tanpa pagination
#     start_time = time.time()
#     cursor.execute("SELECT SaleID, ProductName, SaleDate, Amount FROM SalesData")
#     data = cursor.fetchall()
    
#     conn.close()
    
#     return render_template('dashboard.html', data=data, page=1, total_pages=1, query_time=time.time() - start_time)

# if __name__ == '__main__':
#     app.run(debug=True)