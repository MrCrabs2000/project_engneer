from flask import Flask, request, render_template, redirect, url_for, session, flash

import db_session
from Classes import Item, User
from sqlalchemy.exc import IntegrityError
from tgbotiha import check_response
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = '25112008'
app.config['TELEGRAM_BOT_TOKEN'] = '8373230853:AAExLeEupdgJyfOZV7o3GtUEiAQZxlWVMr0'


os.makedirs('db', exist_ok=True)
db_session.global_init(True, 'db/users.db')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method =='POST':
        username = request.form['username']
        usersurname = request.form['usersurname']
        userclass = request.form['userclass']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if not all([username, usersurname, userclass, password, confirm_password]):
            flash('Все поля обязательны для заполнения', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            return render_template('register.html')

        session = db_session.create_session()

        if session.query(User).filter(User.username == username).first():
            flash('Пользователь с таким именем уже существует', 'error')
            session.close()
            return redirect(url_for('register'))


        try:
            new_user = User(
                username=username,
                usersurname=usersurname,
                userpassword=generate_password_hash(password),
                phonenumber='',
                userclass=userclass,
                role='Student',
                userbalance='0',
                avatar=''
            )
            session.add(new_user)
            session.commit()

            flash('Вы успешно зарегистрировались!', 'success')
        except Exception:
            session.rollback()
            print('deb')
            flash('Ошибка при регистрации!', 'error')
        finally:
            session.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        usersurname = request.form['usersurname']
        password = request.form['password']

        if not all([username, usersurname, password]):
            flash('Все поля обязательны для заполнения', 'error')
            return render_template('register.html')

        session = db_session.create_session()

        user = session.query(User).filter_by(
            username=username,
            usersurname=usersurname,
            userpassword=password
        ).first()
        session.close()

        if user and check_password_hash(user.userpassword, password):
            session['username'] = user.username
            session['usersurname'] = user.usersurname
            session['userclass'] = user.userclass
            session['password'] = user.userpassword
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверные данные для входа', 'error')

    return render_template('login.html')


@app.route('/login/telegram')
def login_telegram():
    data = {
        'id': request.args.get('id', None),
        'first_name': request.args.get('first_name', None),
        'last_name': request.args.get('last_name', None),
        'username': request.args.get('username', None),
        'photo_url': request.args.get('photo_url', None),
        'auth_date': request.args.get('auth_date', None),
        'hash': request.args.get('hash', None)
    }
    if check_response(data):
        return data
    else:
        return 'Ошибка авторизации'


@app.route('/main')
def main_page():
    return render_template('main.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)

