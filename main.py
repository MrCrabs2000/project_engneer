from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_login import logout_user, LoginManager, login_user, current_user
from transliterate import translit
import db_session
from Classes import Item_user, User, Item_shop
from tgbotiha import check_response
from werkzeug.security import generate_password_hash, check_password_hash
import os
from exel import import_users
from datetime import date

# Педелайте роуты, как они ниже расписаны, пожалуйста. Это не только мне надо, но и пользователям.

# @app.route('/login/telegram')

# @app.route('/purchases/<item>')

# @app.toute('/users/distribute')

# @app.route('/items/<item>)
# @app.route('/items/<item>/edit)

# @app.route('/classes/<class>')
# @app.route('/classes/<class>/<student>')

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
    user = session.get(User, user_id)
    session.close()
    return user


@app.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        if current_user.role == 'Student':
            return shop()
        
        elif current_user.role == "Teacher":
            return redirect('/classes') 
         
        elif current_user.role == "Admin":
            return redirect('/users')

    elif not current_user.is_authenticated:
        return redirect('/login')


#STUDENT ROUTES
def shop():
    session_db = db_session.create_session()
    items = session_db.query(Item_shop).all()

    context = {'current_user_role': current_user.role, 
               'items': items, 
               'userbalance': current_user.userbalance}

    session_db.close()

    return render_template('student/shop.html', **context)


@app.route('/shop/<item_id>', methods=['GET', 'POST'])
def item(item_id):
    if current_user.is_authenticated and current_user.role == 'Student':
        session_db = db_session.create_session()
        item_shop = session_db.query(Item_shop).filter_by(id=item_id).first()
        user = session_db.query(User).filter_by(id=current_user.id).first()
        item_user = session_db.query(Item_user).filter_by(id=item_shop.id).first()

        if request.method == 'POST':
            amount = request.form['item_count']

            if int(user.userbalance) >= (int(item_shop.price) * int(amount)) and item_user is None and item_shop.count - int(amount) >= 0:
                user.userbalance = int(user.userbalance) - (int(item_shop.price) * int(amount))
                item_shop.count -= int(amount)

                new_item = Item_user(
                userid=current_user.id,
                status='На рассмотрении',
                name=item_shop.name,
                count=int(amount),
                description=item_shop.description,
                photo=item_shop.photo,
                date=date.today()
                )
                session_db.add(new_item)
                session_db.commit()

            elif (int(user.userbalance) >= (int(item_shop.price) * int(amount))
                  and item_user
                  and item_shop.count - int(amount) >= 0):

                if item_shop.count - int(amount) >= 0:
                    user.userbalance = int(user.userbalance) - (int(item_shop.price) * int(amount))
                    item_shop.count -= int(amount)
                    item_user.count += int(amount)
                    session_db.commit()

        context = {'userbalance': user.userbalance,
                   'current_user_role': current_user.role,
                   'item': item_shop}

        return render_template('admin/items/item.html', **context)

    elif not(current_user.is_authenticated):
        return redirect('/login')


# НУЖНО ОБГОВОРИТЬ ЛОГИКУ
@app.route('/purchases', methods=['GET'])
def purchases():
    if current_user.is_authenticated:
        if current_user.role == 'Student':
            session_db = db_session.create_session()
            user_id = current_user.id
            items_user = session_db.query(Item_user).filter_by(userid=user_id).all()
            items_list = []
            for item in items_user:
                item_data = {
                    'id': item.id,
                    'status': item.status,
                    'name': item.name,
                    'count': item.count,
                    'photo': item.photo,
                    'description': item.description
                }
                items_list.append(item_data)
            print(items_list)
            return render_template('student/purchases.html', items_list=items_list,
                                   current_user_role=current_user.role)
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
            return render_template('student/purchases.html', logged_in=True, username=current_user.username,
                                    usersurname=current_user.usersurname, userclass=current_user.userclass,
                                    userbalance=current_user.userbalance, userotchestvo=current_user.userotchestvo,
                                    all_users=all_users, colvousers=len(all_users),
                                   current_user_role=current_user.role)
        
    elif not(current_user.is_authenticated):
        return redirect('/login')

    
# ADMIN ROUTES
@app.route('/users', methods=['GET', 'POST'])
def users():
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        users = session_db.query(User).all()

        search_text = request.args.get('q', '')
        filterr = request.args.get('filter', 'Фамилия')

        if search_text:
            if filterr == 'Класс':
                users = session_db.query(User).filter(User.userclass.like(f"%{search_text}%")).all()
            elif filterr == 'Фамилия':
                users = session_db.query(User).filter(User.usersurname.like(f"%{search_text}%")).all()
            elif filterr == 'Роль':
                users = session_db.query(User).filter(User.role.like(f"%{search_text}%")).all()

        if request.method == 'POST':
            razdbal = request.form.get('razdbalance')
            if razdbal:
                try:
                    for user in users:
                        if user.role == 'Teacher':
                            user.userbalance = int(user.userbalance) + int(razdbal)
                    session_db.commit()
                except Exception as e:
                    print(f"Галя, у нас ошибка: {e}")
                    session_db.rollback()

        context = {
            'users': users,
            'current_user_role': current_user.role,
            'search_text': search_text,
            'filter': filterr
        }

        session_db.close()
        return render_template('admin/users/users_search.html', **context)

    elif not(current_user.is_authenticated):
        return redirect('/login')


@app.route('/users/<user_id>', methods=['GET'])
def user(user_id):
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()

        user = session_db.query(User).filter_by(id=user_id).first()

        session_db.close()

        context = {'current_user_role': current_user.role,
                   'userbalance': current_user.userbalance,
                   'name': user.username,
                   'surname': user.usersurname,
                   'login': user.userlogin,
                   'otchestvo': user.userotchestvo,
                   'role': user.role,
                   'class': user.userclass,
                   'balance': user.userbalance,
                   'id': user_id}
        
        return render_template('admin/users/user.html', **context)
    
    elif not(current_user.is_authenticated):
        return redirect('/login')
    

@app.route('/users/<user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    if current_user.is_authenticated and current_user.role == 'Admin':
        if request.method == 'GET':
            session_db = db_session.create_session()

            user = session_db.query(User).filter_by(id=user_id).first()

            session_db.close()

            context = {'current_user_role': current_user.role,
                       'userbalance': current_user.userbalance,
                       'name': user.username,
                       'login': user.userlogin,
                       'surname': user.usersurname,
                       'otchestvo': user.userotchestvo,
                       'role': user.role,
                       'class': user.userclass,
                       'balance': user.userbalance,
                       'id': user_id}

            return render_template('admin/users/edit_user.html', **context)
        
        elif request.method == 'POST':
            session_db = db_session.create_session()
            user = session_db.query(User).filter_by(id=user_id).first()

            new_username = request.form['name']
            new_usersurname = request.form['surname']
            new_userotchestvo = request.form['otchestvo']
            new_userclass = request.form['class']
            new_role = request.form['role']
            new_userbalance = request.form['balance']

            if new_usersurname:
                user.usersurname = new_usersurname
            if new_userotchestvo:
                user.userotchestvo = new_userotchestvo
            if new_username:
                user.username = new_username
            if new_userclass:
                user.userclass = new_userclass
            if new_userbalance:
                user.userbalance = new_userbalance
            if new_role:
                user.role = new_role

            user.userlogin = (translit(new_username[:3], 'ru', True)
                              + translit(new_usersurname[:3], 'ru', True)
                              + translit(new_userotchestvo[:3], 'ru', True)
                              + translit(new_userclass, 'ru', True))

            session_db.commit()
            session_db.close()

            return redirect(f'/users/{user_id}')
        
    elif not(current_user.is_authenticated):
        return redirect('/login')

        
@app.route('/users/<user_id>/delete', methods=['GET'])
def delete_user(user_id):
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()

        user = session_db.query(User).filter_by(id=user_id).first()
        session_db.delete(user)
        
        session_db.commit()
        session_db.close()

        return redirect('/users')
    
    elif not(current_user.is_authenticated):
        return redirect('/login')


@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if current_user.is_authenticated and current_user.role == 'Admin':

        if request.method == 'GET' and current_user.adedusers == 'False':
            context = {'current_user_role': current_user.role}
            
            return render_template('admin/users/upload_excel.html', **context)
        
        elif request.method == 'GET' and current_user.adedusers != 'False':
            context = {'current_user_role': current_user.role}

            return render_template('admin/users/add_user.html', **context)

        elif request.method == 'POST':
            
            if len(request.files) > 0:
                file = request.files['inputexel']

                try:
                    file.save('exel/users.xlsx')
                    session_db = db_session.create_session()
                    import_users()
                    users = session_db.query(User).all()
                    for user in users:
                        user.adedusers = True
                        session_db.commit()
                    session_db.close()
                    return redirect('/users')
                except Exception as e:
                    print(f'Галя. у нас ошибка: {e}')
                    return redirect('/users/add')

            else:
                name = request.form['name']
                surname = request.form['surname']
                otchestvo = request.form['otchestvo']
                userclass = request.form['class']
                userbalance = request.form['balance']
                role = request.form['role']
                password = request.form['password']
                secondpassword = request.form['secondpassword']

                userlogin = (translit(name[:3], 'ru', True)
                                  + translit(surname[:3], 'ru', True)
                                  + translit(otchestvo[:3], 'ru', True)
                                  + translit(userclass, 'ru', True))

                if password == secondpassword:
                    new_user = User(
                        username=name,
                        userlogin=userlogin,
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

                    return redirect('/users')
                
    elif not(current_user.is_authenticated):
        return redirect('/login')


@app.route('/items', methods=['GET'])
def items():
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()

        search_text = request.args.get('q', '')
        filterr = request.args.get('filter', 'Название')

        query = session_db.query(Item_shop)

        if search_text:
            if filterr == 'Название':
                items = query.filter(Item_shop.name.like(f"%{search_text}%")).all()
            elif filterr == 'Описание':
                items = query.filter(Item_shop.description.like(f"%{search_text}%")).all()
            elif filterr == 'Цена':
                items = query.filter(Item_shop.price.like(f"%{search_text}%")).all()
            else:
                items = query.all()
        else:
            items = query.all()

        session_db.close()

        context = {'items': items,
                   'current_user_role': current_user.role,
                   'search_text': search_text,
                   'filter': filterr}

        return render_template('admin/items/items_search.html', **context)

    elif not (current_user.is_authenticated):
        return redirect('/login')


@app.route('/items_users', methods=['GET', 'POST'])
def items_users():
    session_db = db_session.create_session()
    users_items = session_db.query(Item_user).all()
    users = []
    for elem in users_items:
        users.append(session_db.query(User).filter_by(id=elem.userid).first())
    session_db.close()
    return render_template('admin/items/items_users.html', users_items=users_items, users=users, kolvo_users=len(users_items))


@app.route('/items/add', methods=['GET', 'POST'])
def add_item():
    if current_user.is_authenticated and current_user.role == 'Admin':
        if request.method == 'GET':
            return render_template('admin/items/add_item.html')
        
        elif request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            count = request.form['count']
            price = request.form['price']
            photo = request.form['photo']

            session_db = db_session.create_session()
            new_item = Item_shop(name=name, description=description, count=count, price=price, photo=photo)
            session_db.add(new_item)
            session_db.commit()
            session_db.close()

            return redirect('/items')
        
    elif not(current_user.is_authenticated):
        return redirect('/login')


@app.route('/items/<item_id>/delete', methods=['POST'])
def delete_item(item_id):
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        item = session_db.query(Item_shop).filter_by(id=item_id).first()
        
        if item:
            session_db.delete(item)
            session_db.commit()

        session_db.close()

        return render_template('admin/items/items_search')

    elif not(current_user.is_authenticated):
        return redirect('/login')


@app.route('/items/<item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        item = session_db.query(Item_shop).filter_by(id=item_id).first()

        if not item:
            session_db.close()
            return redirect('/items')

        if request.method == 'GET':
            context = {
                'current_user_role': current_user.role,
                'name': item.name,
                'description': item.description,
                'count': item.count,
                'price': item.price,
                'photo': item.photo,
                'id': item.id
            }
            session_db.close()
            return render_template('admin/items/edit_item.html', **context)

        elif request.method == 'POST':
            new_name = request.form['name']
            new_description = request.form['description']
            new_count = request.form['count']
            new_price = request.form['price']
            new_photo = request.form['photo']

            if new_name:
                item.name = new_name
            if new_description:
                item.description = new_description
            if new_count:
                item.count = new_count
            if new_price:
                item.price = new_price
            if new_photo:
                item.photo = new_photo

            session_db.commit()
            return redirect(f'/items')

    elif not(current_user.is_authenticated):
        return redirect('/login')


# TEACHER ROUTES
@app.route('/classes')
def classes():
    if current_user.is_authenticated and current_user.role == 'Teacher':
        classes = current_user.userclass.split(' ')

        context = {'current_user_role': current_user.role,
                   'classes': classes,
                   'userbalance': current_user.userbalance,
                   'teacherid': current_user.id}

        return render_template('teacher/classes_list.html', **context, role=current_user.role)
    
    elif not(current_user.is_authenticated):
        return redirect('/login')


# AUTHORIZATION ROUTES
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('authorization/register.html')

    elif request.method == 'POST':
        username = request.form['username']
        usersurname = request.form['usersurname']
        userotchestvo = request.form['userotchestvo']
        userclass = request.form['userclass']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        userlogin = (translit(username[:3], 'ru', True)
                     + translit(usersurname[:3], 'ru', True)
                     + translit(userotchestvo[:3], 'ru', True)
                     + translit(userclass, 'ru', True))

        session_db = db_session.create_session()

        if not all([username, usersurname, userclass, password, confirm_password]):
            flash('Все поля обязательны для заполнения', 'error')
            session_db.close()
            return render_template('authorization/register.html')
        elif password != confirm_password:
            flash('Пароли не совпадают', 'error')
            session_db.close()
            return render_template('authorization/register.html')
        elif len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            session_db.close()
            return render_template('authorization/register.html')
        elif session_db.query(User).filter(User.username == username).first():
            flash('Пользователь с таким именем уже существует', 'error')
            session_db.close()
            return render_template('authorization/register.html')
        
        try:
            new_user = User(username=username,
                            userlogin=userlogin,
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
        
        if current_user.role == 'Student':
            return redirect('/')
        elif current_user.role == 'Teacher':
            return redirect('/classes')
        elif current_user.role == 'Admin':
            return redirect('/users')
        
    elif not(current_user.is_authenticated):
        return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('authorization/login.html')

    elif request.method == 'POST':
        session_db = db_session.create_session()

        login = request.form['login']
        password = request.form['password']
        
        user = session_db.query(User).filter_by(userlogin=login).first()
        
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
            
            if current_user.role == 'Student':
                return redirect('/')
            elif current_user.role == 'Teacher':
                return redirect('/classes')
            elif current_user.role == 'Admin':
                return redirect('/users')
        
        elif not all([login, password]):
            flash('Все поля обязательны для заполнения', 'error')
            session_db.close()

            return render_template('authorization/login.html')
        
        else:
            flash('Неверные имя, фамилия или пароль', 'error')
            session_db.close()

            return render_template('authorization/login.html')
        
    elif not(current_user.is_authenticated):
        return redirect('/login')


@app.route('/logout', methods=['GET'])
def logout():
    if current_user.is_authenticated:
        logout_user()
        
        return redirect('/login')
    
    elif not(current_user.is_authenticated):
        return redirect('/login')
    


# PROFILE ROUTES
@app.route('/profile', methods=['GET'])
def profile():
    if current_user.is_authenticated:
        context = {'username': current_user.username,
                   'usersurname': current_user.usersurname, 
                   'userotchestvo': current_user.userotchestvo,
                   'userclass': current_user.userclass, 
                   'current_user_role': current_user.role,
                   'login': current_user.userlogin}

        return render_template('common/profile/profile.html', **context)
    
    elif not(current_user.is_authenticated):
        return redirect('/login')


@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if current_user.is_authenticated:
        
        if request.method == 'GET':
            context = {'username': current_user.username,
                       'usersurname': current_user.usersurname, 
                       'userotchestvo': current_user.userotchestvo,
                       'userclass': current_user.userclass, 
                       'current_user_role': current_user.role, 
                       'userbalance': current_user.userbalance}
            
            return render_template('common/profile/profile_edit.html', **context)
            
        elif request.method == 'POST':
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

                return redirect('/profile')
            
    elif not(current_user.is_authenticated):
        return redirect('/login')


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



# ^^^ КОММЕНТАРИЯ В САМОМ ВЕРХУ ^^^

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
        if int(teacherid) == int(current_user.id):
            return render_template('teacher/class.html',
                                   logged_in=True,
                                   username=teacher.username,
                                   usersurname=teacher.usersurname,
                                   userclass=teacher.userclass,
                                   userbalance=teacher.userbalance,
                                   userotchestvo=teacher.userotchestvo,
                                   current_user_role=teacher.role,
                                   class_name=class_name,
                                   students=students_list,
                                   students_count=len(students_list),
                                   tid=teacher.id,
                                   adminid='nul')
        else:
            return render_template('teacher/class.html', logged_in=True, username=teacher.username,
                                   usersurname=teacher.usersurname, userclass=teacher.userclass,
                                   userbalance=teacher.userbalance, userotchestvo=teacher.userotchestvo,
                                   role=teacher.role, class_name=class_name, students=students_list,
                                   students_count=len(students_list), tid=teacher.id, adminid=current_user.id)
    return redirect(url_for('login'))


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
                mark = request.form.get('mark')

                marks = {
                    '5': 200,
                    '4': 100,
                    '3': 0,
                    '2': -100
                }

                if mark in marks:
                    balance_change = marks[mark]

                    if balance_change > 0:
                        if int(teacher.userbalance) >= balance_change:
                            user.userbalance = str(int(user.userbalance) + balance_change)
                            teacher.userbalance = str(int(teacher.userbalance) - balance_change)
                            session_db.commit()

                    elif balance_change < 0:
                        balance_abs = abs(balance_change)
                        if int(user.userbalance) >= balance_abs:
                            user.userbalance = str(int(user.userbalance) + balance_change)
                            teacher.userbalance = str(int(teacher.userbalance) + balance_abs)
                            session_db.commit()

            username = user.username
            usersurname = user.usersurname
            userotchestvo = user.userotchestvo
            userclass = user.userclass
            userbalance = user.userbalance
            teacher_balance = teacher.userbalance
            session_db.close()

            return render_template('teacher/student.html',
                                   username=username,
                                   usersurname=usersurname,
                                   userotchestvo=userotchestvo,
                                   userclass=userclass,
                                   userbalance=teacher_balance,
                                   studbalance=userbalance,
                                   iduser=iduser,
                                   teacherid=teacherid,
                                   current_user_role=teacher.role)

        return redirect(url_for('main_page'))

# ^^^ КОММЕНТАРИЯ В САМОМ ВЕРХУ ^^^


@app.route('/enterteach/<userid>')
def enteracc(userid):

    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        teacher = session_db.query(User).filter_by(id=userid).first()
        session_db.close()
        adminid = current_user.id
        return render_template('teacher/classes_list.html', adminid=adminid, teachername=teacher.username,
                               teacersurname=teacher.usersurname, teacherotchestvo=teacher.userotchestvo,
                               role=teacher.role, userbalance=teacher.userbalance, teacherid=teacher.id,
                               teacher_classes=teacher.userclass.split())


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)