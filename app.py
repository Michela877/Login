from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
import mysql.connector
import bcrypt
import pyotp
import os
import datetime
import time

app = Flask(__name__)
app.secret_key = 'il_tuo_segreto'

# Configurazione del database MySQL
db_config = {
    'host': os.getenv('MYSQL_HOST', '40.65.111.152'),
    'port': os.getenv('MYSQL_PORT', '3306'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'SecretPassword'),
    'database': os.getenv('MYSQL_DATABASE', 'asset_management')
}

# Configurazione Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '90michela90@gmail.com'
app.config['MAIL_PASSWORD'] = 'fcwhkmxgpkvnegub'
app.config['MAIL_DEFAULT_SENDER'] = '90michela90@gmail.com'

mail = Mail(app)

def log_event(message):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        timestamp = int(time.time())
        cursor.execute('INSERT INTO logs (timestamp, log) VALUES (%s, %s)', (timestamp, message))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Errore di connessione al database per il logging: {err}")

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            cursor.execute('''
                SELECT l.email, l.credenziali_accesso, d.ruolo
                FROM login l
                JOIN dipendenti d ON l.email = d.email
                WHERE l.email = %s
            ''', (email,))
            account = cursor.fetchone()

            if account:
                if bcrypt.checkpw(password, account['credenziali_accesso'].encode('utf-8')):
                    otp_secret = pyotp.random_base32()
                    totp = pyotp.TOTP(otp_secret)

                    otp_code = totp.now()
                    session['otp_code'] = otp_code
                    session['otp_secret'] = otp_secret
                    session['otp_expiry'] = (datetime.datetime.now() + datetime.timedelta(minutes=5)).timestamp()
                    session['email_temp'] = account['email']
                    session['role_temp'] = account['ruolo']

                    msg = Message('Codice OTP per il login', recipients=[email])
                    msg.body = f'Il tuo codice OTP è: {otp_code}'
                    mail.send(msg)

                    log_event(f"OTP inviato a {email}")
                    
                    return redirect(url_for('verify_otp'))
                else:
                    msg = 'Password errata, riprova.'
                    log_event(f"Password errata per l'email: {email}")
            else:
                msg = 'Utente non trovato, riprova.'
                log_event(f"Utente non trovato per l'email: {email}")

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            msg = f"Errore di connessione al database: {err}"
            log_event(msg)

    return render_template('login.html', msg=msg)

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    msg = ''
    if request.method == 'POST':
        otp = request.form['otp']
        otp_code = session.get('otp_code')
        otp_secret = session.get('otp_secret')
        otp_expiry = session.get('otp_expiry')

        if not otp_code or not otp_secret or not otp_expiry:
            msg = 'Codice OTP scaduto o non valido. Riprova.'
            log_event("Codice OTP scaduto o non valido.")
        elif datetime.datetime.now().timestamp() > otp_expiry:
            msg = 'Codice OTP scaduto. Riprova.'
            log_event("Codice OTP scaduto.")
        elif otp_code == otp:
            session.pop('otp_code', None)
            session.pop('otp_secret', None)
            session.pop('otp_expiry', None)
            session['loggedin'] = True
            session['email'] = session['email_temp']
            session['role'] = session['role_temp']
            session.pop('email_temp', None)
            session.pop('role_temp', None)
            log_event(f"Accesso effettuato per l'email: {session['email']}")
            return redirect(url_for('home'))
        else:
            msg = 'Codice OTP non valido, riprova.'
            log_event("Codice OTP non valido.")

    return render_template('verify_otp.html', msg=msg)

@app.route('/home')
def home():
    if 'loggedin' in session:
        role = session.get('role')
        if role == 'Admin':
            return redirect(url_for('admin'))
        elif role == 'Amministrazione':
            return redirect(url_for('amministrazione'))
        elif role == 'Manager':
            return redirect(url_for('manager'))
        elif role == 'Dipendente':
            return redirect(url_for('dipendente'))
        else:
            flash('Ruolo non riconosciuto.', 'error')
            log_event(f"Ruolo non riconosciuto per l'email: {session['email']}")
            return redirect(url_for('login'))
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'loggedin' in session and session.get('role') == 'Admin':
        return redirect('http://192.168.178.188:5000?email=' + session['email'])
    flash('Accesso non autorizzato.')
    log_event(f"Accesso non autorizzato per l'email: {session.get('email')}")
    return redirect(url_for('login'))

@app.route('/amministrazione')
def amministrazione():
    if 'loggedin' in session and session.get('role') == 'Amministrazione':
        return render_template('amministrazione.html')
    flash('Accesso non autorizzato.')
    log_event(f"Accesso non autorizzato per l'email: {session.get('email')}")
    return redirect(url_for('login'))

@app.route('/manager')
def manager():
    if 'loggedin' in session and session.get('role') == 'Manager':
        return redirect('http://192.168.178.154:10010/?email=' + session['email'])
    flash('Accesso non autorizzato.')
    log_event(f"Accesso non autorizzato per l'email: {session.get('email')}")
    return redirect(url_for('login'))

@app.route('/dipendente')
def dipendente():
    if 'loggedin' in session and session.get('role') == 'Dipendente':
        return redirect('http://192.168.178.162:14000/home?email=' + session['email'])
    flash('Accesso non autorizzato.')
    log_event(f"Accesso non autorizzato per l'email: {session.get('email')}")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=13000)
