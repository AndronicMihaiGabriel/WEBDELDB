from flask import Flask, request, jsonify, session, render_template, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from database import get_connection
from api import api
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user


app = Flask(__name__)
app.register_blueprint(api)
app.secret_key = 'secret_ceva'
bcrypt = Bcrypt(app)
CORS(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username, rol):
        self.id = id
        self.username = username
        self.rol = rol

    def get_id(self):
        if self.id is None:
            raise ValueError("User ID is None")
        return str(self.id)


@app.route('/client/<int:client_id>')
@login_required
def client_details(client_id):
    return render_template('client_detalii.html', client_id=client_id)


@app.route('/dashboard_principal', methods=['GET'])
def dashboard_principal():
    return render_template('dashboard_principal.html')


@app.route('/login_web', methods=['GET', 'POST'])
def login_web():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                'SELECT * FROM userweb WHERE username = %s', (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and bcrypt.check_password_hash(user['password'], password):
                user_obj = User(user['id'], user['username'], user['rol'])
                login_user(user_obj)
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Login greșit")
    except Exception as e:
        return f"<h3>Eroare internă: {str(e)}</h3>", 500

    return render_template('login.html')


@app.route('/register_web', methods=['GET', 'POST'])
def register_web():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        rol = request.form.get('rol')

        if not username or not password or not email:
            return render_template('register.html', error="Completează toate câmpurile!")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id FROM userweb WHERE username = %s', (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return render_template('register.html', error="Username deja există!")

        cursor.execute('SELECT id FROM userweb WHERE email = %s', (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return render_template('register.html', error="Email deja există!")

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute('INSERT INTO userweb (username, password, rol, email) VALUES (%s, %s, %s,%s)',
                       (username, hashed_pw, rol, email))
        conn.commit()
        cursor.close()
        conn.close()
        return render_template('dashboard_principal.html')
    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.rol == 'admin':
        return render_template('dashboard.html', username=current_user.username, rol=current_user.rol)
    elif current_user.rol == 'user':
        return render_template('dashboard_user.html', username=current_user.username, rol=current_user.rol)
    else:
        return render_template('Rol necunoscut'), 403


@app.route('/dashboard_sume')
@login_required
def dashboard_sume():
    return render_template('sume.html')


@app.route('/dashboard_top5')
@login_required
def dashboard_top5():
    return render_template('top5.html')


@app.route('/dashboard_alerte')
@login_required
def dashboard_alerte():
    return render_template('alerte.html')


@login_manager.user_loader
def load_user(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM userweb WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['rol'])
    return None


@app.route('/dashboard_clienti')
@login_required
def dashboard_clienti():
    return render_template('Afisare_Modificare.html')


@app.route('/', methods=['GET'])
def me():
    if 'user_id' in session:
        return jsonify({'user_id': session['user_id'], 'rol': session['rol']}), 200
    else:
        return jsonify({'error': 'Not logged in'}), 401


@app.route('/dashboard_userweb')
@login_required
def dashboard_userweb():
    return render_template('userweb.html')


@app.route('/api/userweb', methods=['GET'])
@login_required
def api_userweb():
    username = request.args.get('username')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if username:
        cursor.execute(
            "SELECT id, username, rol FROM userweb WHERE username LIKE %s", ('%' + username + '%',))
    else:
        cursor.execute("SELECT id, username, rol FROM userweb")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)


@app.route('/api/userweb/<int:id>', methods=['PUT'])
@login_required
def api_userweb_update(id):
    data = request.json
    rol = data.get('rol')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE userweb SET rol=%s WHERE id=%s", (rol, id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})


@app.route('/select_client')
@login_required
def select_client():
    return render_template('select_client.html')


@app.route('/client/<int:client_id>/statistici')
@login_required
def client_statistici(client_id):
    return render_template('client_statistici.html', client_id=client_id)


@app.route('/client/<int:client_id>/consum')
@login_required
def client_consum(client_id):
    return render_template('client_consum.html', client_id=client_id)


if __name__ == '__main__':
    app.run(debug=True)
