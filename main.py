from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_login import logout_user, LoginManager, login_user, current_user
import db_session
from Classes import Item_user, User, Item_shop
from tgbotiha import check_response
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = '25112008'
app.config['TELEGRAM_BOT_TOKEN'] = '83732308533:AAExLeEupdgJyfOZV7o3GtUEiAQZxlWVMr0'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
os.makedirs('db', exist_ok=True)
db_session.global_init(True, 'db/users.db')


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    session.close()
    return user


@app.route('/')
def main_page():
    if current_user.is_authenticated:
        session = db_session.create_session()
        if current_user.role == 'Student':
            return render_template('main.html', logged_in=True, username=current_user.username,
                                   usersurname=current_user.usersurname, userclass=current_user.userclass,
                                   userbalance=current_user.userbalance, userotchestvo=current_user.userotchestvo,
                                   role=current_user.role)
        elif current_user.role == 'Admin':
            users = session.query(User).all()
            all_users = []
            for user in users:
                userr = {}
                userr['id'] = user.id
                userr['username'] = user.username
                userr['userclass'] = user.userclass
                userr['userrole'] = user.role
                userr['userotchestvo'] = user.userotchestvo
                userr['userbalance'] = user.userbalance
                all_users.append(userr.copy())
            session.close()

            return render_template('main.html', logged_in=True, username=current_user.username,
                                   usersurname=current_user.usersurname, userclass=current_user.userclass,
                                   userbalance=current_user.userbalance, userotchestvo=current_user.userotchestvo,
                                   all_users=all_users, colvousers=len(all_users), role=current_user.role)

        elif current_user.role == 'Teacher':
            teacher_classes = current_user.userclass.split(' ')
            return render_template('main.html', logged_in=True, username=current_user.username,
                                   usersurname=current_user.usersurname, userclass=current_user.userclass,
                                   userbalance=current_user.userbalance, userotchestvo=current_user.userotchestvo,
                                   role=current_user.role, teacher_classes=teacher_classes)

    return render_template('index.html')


@app.route('/history')
def history():
    if current_user.is_authenticated:
        session = db_session.create_session()
        if current_user.role == 'Student' or current_user.role == 'Teacher':
            return render_template('history.html', logged_in=True, username=current_user.username,
                                   usersurname=current_user.usersurname, userclass=current_user.userclass,
                                   userbalance=current_user.userbalance, userotchestvo=current_user.userotchestvo,
                                   role=current_user.role)
        else:
            if current_user.role == 'Admin':
                users = session.query(User).all()
                all_users = []
                for user in users:
                    userr = {}
                    userr['id'] = user.id
                    userr['username'] = user.username
                    userr['userclass'] = user.userclass
                    userr['userrole'] = user.role
                    userr['userotchestvo'] = user.userotchestvo
                    userr['userbalance'] = user.userbalance
                    all_users.append(userr.copy())
                session.close()

                return render_template('history.html', logged_in=True, username=current_user.username,
                                       usersurname=current_user.usersurname, userclass=current_user.userclass,
                                       userbalance=current_user.userbalance, userotchestvo=current_user.userotchestvo,
                                       all_users=all_users, colvousers=len(all_users))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        usersurname = request.form['usersurname']
        userotchestvo = request.form['userotchestvo']
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

        session_db = db_session.create_session()

        if session_db.query(User).filter(User.username == username).first():
            flash('Пользователь с таким именем уже существует', 'error')
            session_db.close()
            return redirect(url_for('register'))

        try:
            new_user = User(
                username=username,
                usersurname=usersurname,
                userpassword=generate_password_hash(password),
                userotchestvo=userotchestvo,
                userclass=userclass,
                role='Student',
                userbalance='0',
            )
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            session['usersurname'] = new_user.usersurname
            session['userclass'] = new_user.userclass
            session['role'] = new_user.role
            session['userotchestvo'] = new_user.userotchestvo
            session['userbalance'] = new_user.userbalance
            session_db.add(new_user)
            session_db.commit()
            login_user(new_user)
            flash('Вы успешно зарегистрировались!', 'success')
        except Exception:
            session_db.rollback()
            flash('Ошибка при регистрации!', 'error')
        finally:
            session_db.close()
        return redirect(url_for('main_page'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        usersurname = request.form['usersurname']
        password = request.form['password']

        if not all([username, usersurname, password]):
            flash('Все поля обязательны для заполнения', 'error')
            return render_template('login.html')

        session_db = db_session.create_session()

        user = session_db.query(User).filter_by(
            username=username,
            usersurname=usersurname
        ).first()

        if user and check_password_hash(user.userpassword, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['usersurname'] = user.usersurname
            session['userclass'] = user.userclass
            session['role'] = user.role
            session['userotchestvo'] = user.userotchestvo
            session['userbalance'] = user.userbalance
            session_db.close()
            login_user(user)
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('main_page'))
        else:
            session_db.close()
            flash('Неверные имя, фамилия или пароль', 'error')

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


@app.route('/edit_profile')
def edit_profile():
    return redirect(url_for('main_page'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main_page'))


@app.route('/profile', methods=['GET'])
def profile():
    if request.method == 'GET':
        return render_template('profile.html', username=session['username'],
                               usersurname=session['usersurname'],
                               userclass=session['userclass'],
                               userotchestvo=session['userotchestvo'],
                               role=session['role'],
                               userbalance=session['userbalance'])


@app.route('/profile_edit', methods=['GET', 'POST'])
def profile_edit():
    if request.method == 'POST':
        session_db = db_session.create_session()

        user = session_db.query(User).filter_by(id=current_user.id).first()

        new_username = request.form['username']
        new_usersurname = request.form['usersurname']
        new_userclass = request.form['userclass']

        if user and all([new_usersurname, new_username, new_userclass]):
            user.username = new_username
            user.usersurname = new_usersurname
            user.userclass = new_userclass

            session_db.commit()

            session['username'] = new_username
            session['usersurname'] = new_usersurname
            session['userclass'] = new_userclass

            session_db.close()
            return redirect(url_for('profile'))

    return render_template('profile_edit.html',
                           username=session['username'],
                           usersurname=session['usersurname'],
                           userclass=session['userclass'],
                           userbalance=session['userbalance'],
                           role=session['role'])


@app.route('/user', methods=['GET', 'POST'])
def user():
    render_template('user.html')


@app.route('/<class_name>', methods=['GET'])
def class_page(class_name):
    if current_user.is_authenticated:
        session_db = db_session.create_session()

        students = session_db.query(User).filter(User.userclass == class_name, User.role == 'Student').all()

        students_list = []
        for student in students:
            student_data = {
                'id': student.id,
                'username': student.username,
                'usersurname': student.usersurname,
                'userotchestvo': student.userotchestvo,
                'userbalance': student.userbalance
            }
            students_list.append(student_data)

        session_db.close()

        return render_template('class_board.html',
                               logged_in=True,
                               username=current_user.username,
                               usersurname=current_user.usersurname,
                               userclass=current_user.userclass,
                               userbalance=current_user.userbalance,
                               userotchestvo=current_user.userotchestvo,
                               role=current_user.role,
                               class_name=class_name,
                               students=students_list,
                               students_count=len(students_list),
                               id=current_user.id)

    return redirect(url_for('login'))


@app.route('/student/<id>')
def student_page(id):
    if id:
        return render_template('student.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
