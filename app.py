from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret_key'

conn = sqlite3.connect('users.db', check_same_thread=False)
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            password TEXT
            )
''')
conn.commit()

cur.execute(f"INSERT INTO users(name, email, password) VALUES('admin', 'admin@mail.ru', 'admin')")
conn.commit()

cur.execute('''
CREATE TABLE IF NOT EXISTS posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            author_name TEXT,
            image TEXT
            )
''')
conn.commit()

def add_new_post(title, content, author_name, image):
    cur.execute("INSERT INTO posts(title, content, author_name, image) VALUES(?, ?, ?, ?)", [title, content, author_name, image])
    conn.commit()

def add_user(name, email, password):
    if name != 'admin':
        cur.execute(f"INSERT INTO users(name, email, password) VALUES('{name}', '{email}', '{password}')")
        conn.commit()

def get_user_by_id(user_id):
    cur.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cur.fetchone()

def get_user_by_email(email):
    cur.execute(f"SELECT * FROM users WHERE email = '{email}'")
    return cur.fetchone()

@app.route('/')
def main():
    posts = cur.execute('SELECT * FROM posts').fetchall()
    user_name = session.get('user_name')
    return render_template('main.html', posts = posts, user_name = user_name)

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        user = get_user_by_email(email)
        if user is None:
            add_user(name, email, password)
            session['user_name'] = name
            session['email'] = email 
            return redirect('/profile/')
        else:
            print("Такой пользователь уже есть")
    return render_template('register.html')

@app.route('/login/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = get_user_by_email(email)
        if user is None:
            return render_template('login.html', massage="Аккаунта с такой почты нет")
        if user[3] == password:
            session['user_name'] = user[1]
            session['email'] = user[2]
            return redirect('/profile/')
        else:
            return render_template('login.html', massage="Пароль неправильный")
    return render_template('login.html')

@app.route('/profile/')
def profile():
    return render_template('profile.html', user_name = session['user_name'])

@app.route('/logout/')
def logout():
    session.clear()
    return redirect('/')

@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        author = session['user_name']

        image = request.files['image']
        filename = secure_filename(image.filename)
        image.save(os.path.join('app_dir/static/uploads', filename))

        add_new_post(title, content, author, filename)
        return redirect('/')
    return render_template('/new_post.html')

@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    name = session['user_name']
    cur.execute('DELETE FROM posts WHERE id = ?', [post_id])
    conn.commit()
    return redirect('/')

@app.route('/delete_account/', methods = ['GET', 'POST'])
def delete_account():
    name = session['user_name']
    cur.execute('DELETE FROM users WHERE name = ?', [name])
    cur.execute('DELETE FROM posts WHERE author_name = ?', [name])
    conn.commit()
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run()
