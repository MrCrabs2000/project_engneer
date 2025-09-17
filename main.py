from flask import Flask, request, render_template, redirect, url_for, session, flash
from Classes import init_db, create_session, User
from sqlalchemy.exc import IntegrityError
from tgbotiha import check_response
import os

app = Flask(__name__)
app.config['TELEGRAM_BOT_TOKEN'] = '8373230853:AAExLeEupdgJyfOZV7o3GtUEiAQZxlWVMr0'
app.secret_key = 'your-secret-key-here'


os.makedirs('db', exist_ok=True)
engine = init_db('sqlite:///db/users.db')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        usersurname = request.form.get('usersurname')
        userclass = request.form.get('userclass')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([username, usersurname, userclass, password, confirm_password]):
            flash('Все поля обязательны для заполнения', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            return render_template('register.html')


        db_session = create_session(engine)
        try:
            new_user = User(
                username=username,
                usersurname=usersurname,
                userclass=userclass,
                userpassword=password,
                phonenumber='',
                role='user',
                userbalance='0',
                avatar=''
            )
            db_session.add(new_user)
            db_session.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db_session.rollback()
            flash('Ошибка при регистрации. Возможно, пользователь уже существует.', 'error')
        finally:
            db_session.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        usersurname = request.form.get('usersurname')
        password = request.form.get('password')

        if not all([username, usersurname, password]):
            flash('Все поля обязательны для заполнения', 'error')
            return render_template('login.html')


        db_session = create_session(engine)
        user = db_session.query(User).filter_by(
            username=username,
            usersurname=usersurname,
            userpassword=password
        ).first()
        db_session.close()

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['usersurname'] = user.usersurname
            session['userclass'] = user.userclass
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for(''))
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


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)

