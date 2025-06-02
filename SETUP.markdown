# Setup dan Pengujian Sistem RBAC

Panduan ini berisi langkah-langkah untuk menyiapkan sistem autentikasi dan otorisasi berbasis RBAC menggunakan Flask, HTML, CSS, dan SQL Server Management Studio (SSMS) 21, serta melakukan stress test dengan JMeter dan pengujian performa query dengan SQLQueryStress.

## Prasyarat
- **Python 3.8+**: Unduh dari [python.org](https://www.python.org/).
- **SQL Server dan SSMS 21**: Unduh dari [microsoft.com](https://www.microsoft.com/en-us/sql-server/sql-server-downloads).
- **JMeter**: Unduh dari [jmeter.apache.org](https://jmeter.apache.org/).
- **SQLQueryStress**: Unduh dari [sqlquerystress.com](https://www.sqlquerystress.com/).

## Struktur Proyek
```plaintext
rbac_system/
├── static/
│   └── style.css
├── templates/
│   ├── login.html
│   └── dashboard.html
├── app.py
├── requirements.txt
├── .gitignore
```

## Langkah-Langkah Setup

### 1. Setup Database di SQL Server Management Studio 21
1. **Install SQL Server dan SSMS**:
   - Unduh dan instal SQL Server serta SSMS 21 dari situs resmi Microsoft.
   - Konfigurasikan SSMS dengan Windows Authentication atau SQL Server Authentication.

2. **Buat Database dan Tabel**:
   - Buka SSMS dan sambungkan ke server database.
   - Jalankan script `create_database.sql` untuk membuat database `RBAC_Demo` dan tabel `Users` serta `SalesData` dengan >500.000 row:
     ```sql
     USE master;
     GO

     -- Buat database
     IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'RBAC_Demo')
     BEGIN
         CREATE DATABASE RBAC_Demo;
     END
     GO

     USE RBAC_Demo;
     GO

     -- Tabel Users untuk autentikasi
     CREATE TABLE Users (
         UserID INT IDENTITY(1,1) PRIMARY KEY,
         Username NVARCHAR(50) UNIQUE NOT NULL,
         Password NVARCHAR(255) NOT NULL,
         Role NVARCHAR(20) NOT NULL
     );
     GO

     -- Tabel Data untuk dashboard
     CREATE TABLE SalesData (
         SaleID INT IDENTITY(1,1) PRIMARY KEY,
         ProductName NVARCHAR(100),
         SaleDate DATETIME,
         Amount DECIMAL(10,2),
         CreatedAt DATETIME DEFAULT GETDATE()
     );
     GO

     -- Insert 500.000+ data dummy ke SalesData
     DECLARE @i INT = 1;
     WHILE @i <= 500000
     BEGIN
         INSERT INTO SalesData (ProductName, SaleDate, Amount)
         VALUES (
             'Product_' + CAST(@i AS NVARCHAR(10)),
             DATEADD(DAY, -RAND() * 365, GETDATE()),
             RAND() * 1000
         );
         SET @i = @i + 1;
     END
     GO

     -- Insert contoh user
     INSERT INTO Users (Username, Password, Role)
     VALUES 
         ('admin', 'admin123', 'Admin'),
         ('user1', 'user123', 'User');
     GO
     ```
   - Verifikasi jumlah row: `SELECT COUNT(*) FROM SalesData;` (harus >500.000).

### 2. Setup Backend dengan Flask
1. **Install Dependensi**:
   - Buka terminal di folder proyek (`rbac_system`).
   - Install dependensi:
     ```bash
     pip install flask pyodbc
     ```
   - Simpan dependensi ke `requirements.txt`:
     ```bash
     pip freeze > requirements.txt
     ```

2. **Konfigurasi app.py**:
   - Pastikan file `app.py` sudah ada dengan kode berikut:
     ```python
     from flask import Flask, request, render_template, redirect, url_for, session
     import pyodbc
     import time

     app = Flask(__name__)
     app.secret_key = 'your_secret_key'

     # Konfigurasi koneksi ke SQL Server
     conn_str = (
         "DRIVER={ODBC Driver 17 for SQL Server};"
         "SERVER=your_server_name;"  # Ganti dengan nama server Anda
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
     @app.route('/dashboard')
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
     ```
   - Ganti `your_server_name` dengan nama server SQL Anda (misalnya, `localhost` atau `DESKTOP-XXXX\SQLEXPRESS`).

3. **Setup Frontend**:
   - Pastikan folder `static` berisi `style.css` dan folder `templates` berisi `login.html` serta `dashboard.html`. (Kode file sudah disediakan di proyek.)
   - Struktur folder:
     ```plaintext
     static/
     └── style.css
     templates/
     ├── login.html
     └── dashboard.html
     ```

4. **Jalankan Aplikasi**:
   - Jalankan Flask:
     ```bash
     python app.py
     ```
   - Akses aplikasi di `http://localhost:5000`.
   - Login dengan `admin`/`admin123` untuk dashboard (role Admin).

### 3. Stress Test dengan JMeter
1. **Install JMeter**:
   - Unduh dan ekstrak JMeter dari [situs resmi](https://jmeter.apache.org/).
   - Jalankan `jmeter.bat` (Windows) atau `./jmeter.sh` (Linux/Mac).

2. **Buat Test Plan**:
   - Buka JMeter, tambahkan **Thread Group**:
     - **Number of Threads**: 10, 100, 1000 (uji secara terpisah).
     - **Ramp-up Period**: 10 detik.
     - **Loop Count**: 10.
   - Tambahkan **HTTP Request**:
     - **Server Name**: `localhost`.
     - **Port**: `5000`.
     - **Path**:
       - Dengan pagination: `/dashboard?page=1`.
       - Tanpa pagination: Modifikasi `app.py` untuk menghapus OFFSET/FETCH, gunakan `/dashboard`.
     - **Method**: GET.
   - Tambahkan **HTTP Cookie Manager** untuk session.
   - Tambahkan **Listener** (misalnya, **Summary Report**, **View Results Tree**, **Aggregate Report**).

3. **Jalankan Test**:
   - Uji dengan pagination dan tanpa pagination untuk 10, 100, dan 1000 user.
   - Catat metrik: **Average Response Time**, **Throughput**, **Error Rate**.
   - **Contoh Modifikasi app.py untuk Tanpa Pagination**:
     ```python
     # Ganti query di route /dashboard
     cursor.execute("SELECT SaleID, ProductName, SaleDate, Amount FROM SalesData")
     data = cursor.fetchall()
     ```
     Kembalikan ke versi pagination setelah pengujian.

4. **Analisis Hasil**:
   - Pagination: Response time lebih cepat karena hanya mengambil 100 row.
   - Tanpa pagination: Lebih lambat, terutama pada 1000 user.

### 4. Pengujian Performa Query dengan SQLQueryStress
1. **Install SQLQueryStress**:
   - Unduh dari [sqlquerystress.com](https://www.sqlquerystress.com/).

2. **Query Awal**:
   ```sql
   SELECT SaleID, ProductName, SaleDate, Amount 
   FROM SalesData 
   ORDER BY SaleID 
   OFFSET 0 ROWS FETCH NEXT 100 ROWS ONLY;
   ```

3. **Konfigurasi Pengujian**:
   - Buka SQLQueryStress, masukkan query di atas.
   - **Koneksi**: Server SQL Anda, database `RBAC_Demo`.
   - **Parameter**:
     - **Number of Threads**: 10, 50, 100.
     - **Number of Iterations**: 1000 per thread.
     - **Delay**: 0 ms.
   - Jalankan tes, catat **Average Execution Time**, **Total Time**, dan **Errors**.

4. **Optimasi Query**:
   - Tambahkan indeks:
     ```sql
     CREATE NONCLUSTERED INDEX IX_SalesData_SaleID 
     ON SalesData(SaleID);
     ```
   - Ulangi pengujian dengan parameter yang sama.

5. **Bandingkan Hasil**:
   - **Sebelum Indeks**: Lambat karena full table scan.
   - **Sesudah Indeks**: Lebih cepat (biasanya 5-10x lebih cepat).
   - Contoh hasil:
     - 10 threads: ~500 ms → ~50 ms.
     - 50 threads: ~2000 ms → ~200 ms.
     - 100 threads: ~5000 ms → ~500 ms.

## Catatan Tambahan
- **Keamanan**: Gunakan hashing password di produksi (misalnya, bcrypt).
- **Skalabilitas**: Gunakan Gunicorn untuk server produksi:
  ```bash
  pip install gunicorn
  gunicorn -w 4 app:app
  ```
- **Pengujian**:
  - Pagination lebih efisien untuk dataset besar.
  - Indeks pada `SaleID` sangat meningkatkan performa query.
- **Lisensi**: File `LICENSE` menggunakan MIT License (sudah disediakan).
