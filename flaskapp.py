# importing modules
import sqlite3
from flask import Flask, render_template, g, request, redirect, url_for
import os
from flask import send_file
from werkzeug.utils import secure_filename

DATABASE = '/var/www/html/flaskapp/users.db'
UPLOAD_FOLDER = '/home/ubuntu/flaskapp/uploads'
app = Flask(__name__)
app.config.from_object(__name__)

def connect_to_database():
    return sqlite3.connect(app.config['DATABASE'])

def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = g.db = connect_to_database()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def execute_query(query, args=()):
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return rows

def commit():
    get_db().commit()

def get_user_folder_word_count(username):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(username))
    wc = "0"
    try:
        with open(os.path.join(user_folder, 'Limerick.txt'), 'r') as wc_file:
            wc = wc_file.read().strip()
    except FileNotFoundError:
        pass
    return wc

def cntWords(file_path_or_content):
    with open(file_path_or_content, 'r') as file:
        string = file.read()
        words = string.split()
        return str(len(words))

@app.route('/')
def mainpage():
    return render_template('mainpage.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Retrieve form data
    username = request.form['username']
    password = request.form['password']
    CHECK_USER = ''' SELECT * FROM users WHERE username=?'''
    wc = 0
    user_exists = execute_query(CHECK_USER, (username,))
    commit()
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(username))
    if user_exists:
        wc = get_user_folder_word_count(username)
        return redirect(url_for('display_details', username=username, password=password, wc=wc))

    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']

    CREATE_TABLE =  '''
                        CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        first_name TEXT,
                        last_name TEXT,
                        email TEXT
                         )
                    '''
    INSERT_INTO_TABLE = '''
                                INSERT INTO users (username, password, first_name, last_name, email)
                                VALUES (?, ?, ?, ?, ?)
                        '''
    CHECK_USER = ''' SELECT * FROM users WHERE username=?'''
    execute_query(CREATE_TABLE)

    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    nfile = request.files['textfile']
    file_path = os.path.join(user_folder, secure_filename(nfile.filename))
    nfile.save(file_path)

    wc = cntWords(file_path)

    user_exists = execute_query(CHECK_USER, (username,))
    commit()

    if user_exists:
        return redirect(url_for('display_details', username=username, password=password, wc=wc))

    res = execute_query(INSERT_INTO_TABLE, (username, password, first_name, last_name, email))
    commit()

    return redirect(url_for('display_details', username=username, password=password, wc=wc))

def get_all_txt_files_in_folder(folder_path):
    try:
        txt_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.endswith('.txt')]
        return txt_files
    except FileNotFoundError:
        return []

@app.route('/display_details')
def display_details():
    username = request.args.get('username')
    password = request.args.get('password')
    wc = request.args.get('wc')
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(username))
    file_details = get_all_txt_files_in_folder(user_folder)
    print('**********************************')
    print(file_details)
    print('**********************************')
    if len(file_details) == 0:
        wc = 0
    else:
        sum1 = 0
        for i in file_details:
            sum1 += int(cntWords(os.path.join(user_folder, i)))
        wc = sum1

    FETCH_DETAILS = '''
                        SELECT * FROM  users  WHERE  username=? AND password=?
                    '''
    user_inf = execute_query(FETCH_DETAILS, (username, password))
    commit()

    return render_template('display_details.html', user_info=user_inf, wc=wc)

@app.route('/download/<username>')
def download_file(username):
    print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
    print(username)
    print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(username))
    file_details = get_all_txt_files_in_folder(user_folder)
    print(user_folder + file_details[0])
    return send_file(user_folder + "/"+file_details[0], as_attachment=True)

@app.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
