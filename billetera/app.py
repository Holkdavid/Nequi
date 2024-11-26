from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from datetime import datetime

# Inicializa la aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'  # Cambia 'root' por tu usuario de MySQL
app.config['MYSQL_PASSWORD'] = 'holamundo'  # Cambia por tu contraseña
app.config['MYSQL_DB'] = 'billetera_digital'
app.secret_key = 'supersecretkey'

# Inicializa MySQL
mysql = MySQL(app)

### Rutas de la Aplicación ###

# Página de inicio
@app.route('/')
def index():
    return render_template('index.html')  # Crea 'index.html' en la carpeta 'templates'

# Registro de usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO usuarios (nombre, email, telefono, contraseña) VALUES (%s, %s, %s, %s)', 
                       (nombre, email, telefono, password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))
    
    return render_template('register.html')  # Crea 'register.html' en la carpeta 'templates'

# Inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE email = %s AND contraseña = %s', (email, password))
        usuario = cursor.fetchone()
        cursor.close()

        if usuario:
            session['user_id'] = usuario[0]  # Asume que el ID del usuario está en la primera columna
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Credenciales inválidas.")
    
    return render_template('login.html')  # Crea 'login.html' en la carpeta 'templates'

# Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Dashboard del usuario (consulta de saldo)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT saldo FROM cuentas WHERE id_usuario = %s', [user_id])
    saldo = cursor.fetchone()[0]
    cursor.close()
    
    return render_template('dashboard.html', saldo=saldo)  # Crea 'dashboard.html' en la carpeta 'templates'

# Página de transacciones
@app.route('/transacciones', methods=['GET', 'POST'])
def transacciones():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        tipo = request.form['tipo']
        monto = float(request.form['monto'])
        cuenta_destino = request.form.get('cuenta_destino')

        cursor = mysql.connection.cursor()
        # Manejo de la transacción dependiendo del tipo
        if tipo == 'retiro':
            cursor.execute('UPDATE cuentas SET saldo = saldo - %s WHERE id_usuario = %s AND saldo >= %s', (monto, user_id, monto))
        elif tipo == 'consignacion' and cuenta_destino:
            cursor.execute('UPDATE cuentas SET saldo = saldo - %s WHERE id_usuario = %s AND saldo >= %s', (monto, user_id, monto))
            cursor.execute('UPDATE cuentas SET saldo = saldo + %s WHERE id_cuenta = %s', (monto, cuenta_destino))
        
        # Registro de la transacción
        cursor.execute('INSERT INTO transacciones (id_cuenta_origen, id_cuenta_destino, monto, tipo, fecha) VALUES (%s, %s, %s, %s, NOW())',
                       (user_id, cuenta_destino, monto, tipo))
        
        mysql.connection.commit()
        cursor.close()
    
    return render_template('transacciones.html')  # Crea 'transacciones.html' en la carpeta 'templates'

### Ejecutar la aplicación ###
if __name__ == '__main__':
    app.run(debug=True)
