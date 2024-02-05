#importing modules
import sqlite3
from flask import Flask, render_template, g, request,redirect, url_for
import os


DATABASE = '/var/www/html/flaskapp/users.db'
UPLOAD_FOLDER = 'uploads'
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
@app.route('/')
def mainpage():
    return render_template('mainpage.html')


@app.route('/submit', methods=['POST'])
def submit():
    # Retrieve form data
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']

    # Storing the information in the database
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
    CHECK_USER = ''' SELECT * FROM users WHERE username=?'''
    execute_query(CREATE_TABLE)

    nfile = request.files['textfile']
    wc = "0" #default val
    if nfile:
         wc = cntWords(nfile)

    print("debug word count === ", wc)

    user_exists = execute_query(CHECK_USER, (username,))
    commit()

    print("res from user exists", user_exists)
    if user_exists:
        return redirect(url_for('display_details', username=username, password=password, wc=wc))


    res = execute_query(CREATE_TABLE)
    print("res from db create", res)
    commit()

    res = execute_query(INSERT_INTO_TABLE, (username, password, first_name, last_name, email))
    print("res from db insert", res)
    commit()
    
    return redirect(url_for('display_details', username=username, password=password, wc=wc))
@app.route('/display_details')
def display_details():
    
    username = request.args.get('username')
    password = request.args.get('password')
    wc = request.args.get('wc')


    FETCH_DETAILS = '''
                        SELECT * FROM  users  WHERE  username=? AND password=?
                    '''
    user_inf=execute_query(FETCH_DETAILS, (username, password))
    commit()

    print("res from db fetch user_inf", user_inf)
    return render_template('display_details.html', user_info=user_inf, wc=wc)


def cntWords(nfile):
    string = nfile.read()
    words = string.split()
    return str(len(words))


if __name__ == '__main__':
       app.run(debug=True)
