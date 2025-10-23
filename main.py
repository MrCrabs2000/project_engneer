from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_login import logout_user, LoginManager, login_user, current_user
import db_session
from Classes import Item_user, User, Item_shop
from tgbotiha import check_response
from werkzeug.security import generate_password_hash, check_password_hash
import os
from exel import import_users


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


@app.route('/', methods=['GET', 'POST'])
def main_page():
    if current_user.is_authenticated:
        session = db_session.create_session()
        if current_user.role == 'Student':
            session_db = db_session.create_session()
            items = session_db.query(Item_shop).all()
            return render_template('shop/shop.html', logged_in=True, username=current_user.username,
                                   usersurname=current_user.usersurname, userclass=current_user.userclass,
                                   userbalance=current_user.userbalance, userotchestvo=current_user.userotchestvo,
                                   role=current_user.role, items=items)
        elif current_user.role == 'Admin':
            users = session.query(User).all()
            all_users = []
            for user in users:
                if user.adedusers == 'False':
                    user.adedusers = False
                    session.commit()
            print(str(current_user.adedusers))
            for user in users:
                userr = {}
                userr['id'] = user.id
                userr['username'] = user.username
                userr['usersurname'] = user.usersurname
                userr['userclass'] = user.userclass
                userr['role'] = user.role
                userr['userotchestvo'] = user.userotchestvo
                userr['userbalance'] = user.userbalance
                all_users.append(userr.copy())
            session.close()
            if request.method == 'POST':
                try:
                    razdbal = request.form['razdbalance']
                    for user in all_users:
                        if user['role'] == 'Teacher':
                            session_db = db_session.create_session()
                            userr = session_db.query(User).filter_by(id=user['id']).first()
                            user['userbalance'] = int(user['userbalance']) + int(razdbal)
                            userr.userbalance = user['userbalance']
                            session_db.commit()
                            session_db.close()
                except Exception:
                    sort = request.form['sort']
                    bysort = request.form['bysort']
                    session_db = db_session.create_session()
                    if sort == 'Класс':
                        all_users = session_db.query(User).filter_by(userclass=bysort).all()
                    elif sort == 'Фамилия':
                        all_users = session_db.query(User).filter_by(usersurname=bysort).all()
                    else:
                        all_users = session_db.query(User).filter_by(role=bysort).all()
                    session_db.close()
                finally:
                    return render_template('admin/users_search.html', logged_in=True, username=current_user.username,
                                           usersurname=current_user.usersurname, userclass=current_user.userclass,
                                           userbalance=current_user.userbalance,
                                           userotchestvo=current_user.userotchestvo, adedusers=str(current_user.adedusers),
                                           all_users=all_users, colvousers=len(all_users), role=current_user.role)
            return render_template('admin/users_search.html', logged_in=True, username=current_user.username,
                                   usersurname=current_user.usersurname, userclass=current_user.userclass,
                                   userbalance=current_user.userbalance, userotchestvo=current_user.userotchestvo,
                                   all_users=all_users, colvousers=len(all_users), role=current_user.role)
        elif current_user.role == 'Teacher':
            teacher_classes = current_user.userclass.split(' ')
            return render_template('classes/classes_list.html', logged_in=True, username=current_user.username,
                                   usersurname=current_user.usersurname, userclass=current_user.userclass,
                                   userbalance=current_user.userbalance, userotchestvo=current_user.userotchestvo,
                                   role=current_user.role, teacher_classes=teacher_classes, teacherid=current_user.id)
    return render_template('sign/sign.html')


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
            users = session.query(User).all()
            all_users = []
            for user in users:
                userr = {}
                userr['id'] = user.id
                userr['username'] = user.username
                userr['userclass'] = user.userclass
                userr['role'] = user.role
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
            return render_template('sign/register.html')
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('sign/register.html')
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            return render_template('sign/register.html')
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
                userbalance=0,)
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
    return render_template('sign/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        usersurname = request.form['usersurname']
        userotchestvo = request.form['userotchestvo']
        password = request.form['password']
        if not all([username, usersurname, password]):
            flash('Все поля обязательны для заполнения', 'error')
            return render_template('sign/login.html')
        session_db = db_session.create_session()
        user = session_db.query(User).filter_by(
            username=username,
            usersurname=usersurname,
            userotchestvo=userotchestvo).first()
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
    return render_template('sign/login.html')


@app.route('/login/telegram')
def login_telegram():
    data = {
        'id': request.args.get('id', None),
        'first_name': request.args.get('first_name', None),
        'last_name': request.args.get('last_name', None),
        'username': request.args.get('username', None),
        'photo_url': request.args.get('photo_url', None),
        'auth_date': request.args.get('auth_date', None),
        'hash': request.args.get('hash', None)}
    if check_response(data):
        return data
    else:
        return 'Ошибка авторизации'


@app.route('/edit_profile')
def edit_profile():
    if current_user.is_authenticated:
        return redirect(url_for('main_page'))


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect(url_for('main_page'))


@app.route('/profile', methods=['GET'])
def profile():
    if current_user.is_authenticated:
        if request.method == 'GET':
            return render_template('profile.html', username=session['username'],
                                   usersurname=session['usersurname'],
                                   userclass=session['userclass'],
                                   userotchestvo=session['userotchestvo'],
                                   role=session['role'],
                                   userbalance=session['userbalance'])


@app.route('/profile_edit', methods=['GET', 'POST'])
def profile_edit():
    if current_user.is_authenticated:
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


@app.route('/<class_name>/<teacherid>', methods=['GET'])
def class_page(class_name, teacherid):
    if current_user.is_authenticated and (current_user.role == 'Teacher' or current_user.role == 'Admin'):
        session_db = db_session.create_session()
        teacher = session_db.query(User).filter_by(id=teacherid).first()
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
        if teacherid == current_user.id:
            return render_template('class.html',
                                   logged_in=True,
                                   username=teacher.username,
                                   usersurname=teacher.usersurname,
                                   userclass=teacher.userclass,
                                   userbalance=teacher.userbalance,
                                   userotchestvo=teacher.userotchestvo,
                                   role=teacher.role,
                                   class_name=class_name,
                                   students=students_list,
                                   students_count=len(students_list),
                                   tid=teacher.id,
                                   adminid='nul')
        else:
            return render_template('class.html', logged_in=True, username=teacher.username,
                                   usersurname=teacher.usersurname, userclass=teacher.userclass,
                                   userbalance=teacher.userbalance, userotchestvo=teacher.userotchestvo,
                                   role=teacher.role, class_name=class_name, students=students_list,
                                   students_count=len(students_list), tid=teacher.id, adminid=current_user.id)
    return redirect(url_for('login'))


@app.route('/userprofile/<userid>')
def userprof(userid):
    if current_user.is_authenticated:
        session_db = db_session.create_session()
        user = session_db.query(User).filter_by(id=userid).first()
        session_db.close()
        return render_template('user.html', user=user, role=current_user.role, userbalance=current_user.userbalance)


@app.route('/itemshop/<itemid>')
def itemshop(itemid):
    if current_user.is_authenticated:
        session_db = db_session.create_session()
        item = session_db.query(Item_shop).filter_by(id=itemid).first()
        return render_template('items.html', userbalance=current_user.userbalance, role=current_user.role,
                               item=item)


@app.route('/edituser/<userid>', methods=['GET', 'POST'])
def edituser(userid):
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        user = session_db.query(User).filter_by(id=userid).first()
        if request.method == 'POST':
            nusername = request.form['name']
            nusersurname = request.form['surname']
            nuserotchestvo = request.form['otchestvo']
            nuserclass = request.form['class']
            nrole = request.form['role']
            nuserbalance = request.form['balance']
            if nusersurname:
                user.usersurname = nusersurname
            if nuserotchestvo:
                user.userotchestvo = nuserotchestvo
            if nusername:
                user.username = nusername
            if nuserclass:
                user.userclass = nuserclass
            if nuserbalance:
                user.userbalance = nuserbalance
            if nrole:
                user.role = nrole
            session_db.commit()
            return redirect(url_for('userprof', userid=user.id))
        session_db.close()
        return render_template('edituser.html', user=user)


@app.route('/student/<iduser>/<teacherid>', methods=['GET', 'POST'])
def student_page(iduser, teacherid):
    if current_user.is_authenticated and (current_user.role == 'Teacher' or current_user.role == 'Admin'):
        if iduser:
            session_db = db_session.create_session()
            user = session_db.query(User).filter_by(id=iduser).first()
            teacher = session_db.query(User).filter_by(id=teacherid).first()
            if not user or not teacher:
                session_db.close()
                return redirect(url_for('main_page'))
            if request.method == 'POST':
                stud_balance = request.form.get('stud_balance')
                action = request.form.get('action')
                if stud_balance and stud_balance.isdigit():
                    balance_change = int(stud_balance)
                    if balance_change <= 0:
                        flash("Сумма должна быть положительной", "error")
                    else:
                        if action == '+':
                            if int(teacher.userbalance) >= balance_change:
                                user.userbalance = str(int(user.userbalance) + balance_change)
                                teacher.userbalance = str(int(teacher.userbalance) - balance_change)
                                session_db.commit()

                        elif action == '-':
                            if int(user.userbalance) >= balance_change:
                                user.userbalance = str(int(user.userbalance) - balance_change)
                                teacher.userbalance = str(int(teacher.userbalance) + balance_change)
                                session_db.commit()
            username = user.username
            usersurname = user.usersurname
            userclass = user.userclass
            userbalance = user.userbalance
            teacher_balance = teacher.userbalance
            session_db.close()
            return render_template('student.html',
                                   username=username,
                                   usersurname=usersurname,
                                   userclass=userclass,
                                   userbalance=teacher_balance,
                                   studbalance=userbalance,
                                   iduser=iduser, teacherid=teacherid)

        return redirect(url_for('main_page'))


@app.route('/deluser/<iduser>')
def deluser_page(iduser):
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        user = session_db.query(User).filter_by(id=iduser).first()
        session_db.delete(user)
        session_db.commit()
        session_db.close()
        return redirect(url_for('main_page'))


@app.route('/adduser', methods=['GET', 'POST'])
def adduser():
    if current_user.is_authenticated and current_user.role == 'Admin':
        if request.method == 'POST':
            name = request.form['name']
            surname = request.form['surname']
            otchestvo = request.form['otchestvo']
            userclass = request.form['class']
            userbalance = request.form['balance']
            role = request.form['role']
            password = request.form['password']
            secondpassword = request.form['secondpassword']
            if password == secondpassword:
                new_user = User(
                    username=name,
                    usersurname=surname,
                    userpassword=generate_password_hash(password),
                    userotchestvo=otchestvo,
                    userclass=userclass,
                    role=role,
                    userbalance=userbalance,
                )
                session_db = db_session.create_session()
                session['user_id'] = new_user.id
                session['username'] = new_user.username
                session['usersurname'] = new_user.usersurname
                session['userclass'] = new_user.userclass
                session['role'] = new_user.role
                session['userotchestvo'] = new_user.userotchestvo
                session['userbalance'] = new_user.userbalance
                session_db.add(new_user)
                session_db.commit()
                return redirect(url_for('main_page'))
        return render_template('adduser.html')


@app.route('/enterteach/<userid>')
def enteracc(userid):
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        teacher = session_db.query(User).filter_by(id=userid).first()
        session_db.close()
        adminid = current_user.id
        return render_template('classes/classes_list.html', adminid=adminid, teachername=teacher.username,
                               teacersurname=teacher.usersurname, teacherotchestvo=teacher.userotchestvo,
                               role=teacher.role, userbalance=teacher.userbalance, teacherid=teacher.id,
                               teacher_classes=teacher.userclass.split())


@app.route('/addingusers')
def addusers():
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        import_users()
        users = session_db.query(User).all()
        for user in users:
            user.adedusers = True
            session_db.commit()
        session_db.close()
        return redirect(url_for('main_page'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)