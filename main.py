from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_login import logout_user, LoginManager, login_user, current_user
from transliterate import translit
import db_session
from Classes import Item_user, User, Item_shop
from werkzeug.security import generate_password_hash, check_password_hash
import os
from exel import import_users, generate_password_for_user
from datetime import date
import copy


app = Flask(__name__)
app.secret_key = '25112008'
app.config['FOLDER'] = 'static/images/items_images'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
os.makedirs('db', exist_ok=True)
os.makedirs('images', exist_ok=True)
os.makedirs('images/items_images', exist_ok=True)
db_session.global_init(True, 'db/users.db')


session_db = db_session.create_session()
admin = session_db.query(User).filter_by(userlogin='Admin').first()
try:
    if not admin:
        password = generate_password_for_user()
        print(password)

        passwordHash = generate_password_hash(password)

        main_admin = User(
            username='Admin',
            usersurname='Admin',
            userotchestvo='Admin',
            userlogin='Admin',
            userpassword=passwordHash,
            role='Admin',
            userbalance='0',
            userclass='x',
            adedusers='False'
        )

        session_db.add(main_admin)
        session_db.commit()
except Exception:
    session_db.rollback()
session_db.close()


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
        item_shop = session_db.query(Item_shop).filter_by(id=int(item_id)).first()
        user = session_db.query(User).filter_by(id=current_user.id).first()

        if not item_shop:
            session_db.close()
            return redirect('/')

        if request.method == 'POST':
            amount = request.form['item_count']

            if (int(user.userbalance) >= (int(item_shop.price) * int(amount))
                    and item_shop.count >= int(amount)):

                user.userbalance = int(user.userbalance) - (int(item_shop.price) * int(amount))
                item_shop.count -= int(amount)

                ddate = date.today().strftime('%d-%m-%Y')

                new_item = Item_user(
                    userid=current_user.id,
                    itemshopid = item_shop.id,
                    status='Принята',
                    count=int(amount),
                    date=ddate
                )
                print(item_shop.id)

                session_db.add(new_item)
                session_db.commit()

                

                session_db.close()
                return redirect('/shop/successful-purchase')
            else:
                flash('Недостаточно средств или товара', 'error')

        context = {'userbalance': user.userbalance,
                   'current_user_role': current_user.role,
                   'item': item_shop}

        session_db.close()
        return render_template('admin/items/item.html', **context)

    elif not current_user.is_authenticated:
        return redirect('/login')


@app.route('/shop/successful-purchase', methods=['GET'])
def show_successful_purchase():
    context = {'userbalance': current_user.userbalance,
                'current_user_role': current_user.role}

    return render_template('student/successful_purchase.html', **context)


@app.route('/purchases', methods=['GET'])
def purchases():
    if current_user.is_authenticated:
        if current_user.role == 'Student':
            session_db = db_session.create_session()
            user_id = current_user.id
            items_user = session_db.query(Item_user).filter_by(userid=user_id).all()
            items_list = []
            for item in items_user:
                item_shop = session_db.query(Item_shop).filter_by(id=int(item.itemshopid)).first()
                item_data = {
                    'id': item.id,
                    'status': item.status,
                    'itemshopid': item.itemshopid,
                    'count': item.count,
                    'date': item.date,
                    'name': item_shop.name
                }
                items_list.append(item_data)
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
        
    elif not current_user.is_authenticated:
        return redirect('/login')

    
# ADMIN ROUTES
@app.route('/users', methods=['GET', 'POST'])
def users():
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        users = session_db.query(User).all()

        search_text = request.args.get('q', '')
        filterr = request.args.get('filter', 'Фамилия')

        if search_text and filterr:
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

            session_db.close()

            return redirect(f'/users?q={search_text}&filter={filterr}')
        

        context = {
            'users': copy.deepcopy(users),
            'current_user_role': current_user.role,
            'search_text': search_text,
            'filter': filterr
        }

        session_db.close()

        return render_template('admin/users/users_search.html', **context)

    elif not current_user.is_authenticated:
        return redirect('/login')


@app.route('/users/<user_id>', methods=['GET'])
def user(user_id):
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()

        user = session_db.query(User).filter_by(id=user_id).first()

        session_db.close()

        context = {'current_user_role': current_user.role,
                   'name': user.username,
                   'surname': user.usersurname,
                   'login': user.userlogin,
                   'otchestvo': user.userotchestvo,
                   'role': user.role,
                   'class': user.userclass,
                   'balance': user.userbalance,
                   'id': user_id}
        if current_user.role == 'Teacher':
            context['class'] = context['class'].split()
        
        return render_template('admin/users/user.html', **context)
    
    elif not current_user.is_authenticated:
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
    elif not current_user.is_authenticated:
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
    
    elif not current_user.is_authenticated:
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
                
    elif not current_user.is_authenticated:
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
                items_archived = [x for x in items if x.is_archived]
            elif filterr == 'Описание':
                items = query.filter(Item_shop.description.like(f"%{search_text}%")).all()
                items_archived = [x for x in items if x.is_archived]
            elif filterr == 'Цена':
                items = query.filter(Item_shop.price.like(f"%{search_text}%")).all()
                items_archived = [x for x in items if x.is_archived]
            else:
                items = query.all()
                items_archived = [x for x in items if x.is_archived]
        else:
            items = query.all()
            items_archived = [x for x in items if x.is_archived]

        session_db.close()

        context = {'items': items,
                   'items_archived': items_archived,
                   'current_user_role': current_user.role,
                   'search_text': search_text,
                   'filter': filterr}

        return render_template('admin/items/items_search.html', **context)

    elif not current_user.is_authenticated:
        return redirect('/login')


@app.route('/items_users', methods=['GET', 'POST'])
def items_users():
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        users_items = session_db.query(Item_user).all()
        users = []
        for elem in users_items:
            users.append(session_db.query(User).filter_by(id=elem.userid).first())
        session_db.close()

        items = []
        for i in range(len(users)):
            items.append({'item': users_items[i], 'user': users[i]})

        context = {'items': items,
                   'current_user_role': current_user.role,
                   }

        return render_template('admin/items/items_users.html', **context)
    elif not current_user.is_authenticated:
        return redirect('/login')


@app.route('/items_users/<item_id>')
def item_user(item_id):
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        item = session_db.query(Item_user).filter_by(id=item_id).first()
        user = session_db.query(User).filter_by(id=item.userid).first()
        item_shop = session_db.query(Item_shop).filter_by(id=item.shopid).first()
        session_db.close()
        return render_template('admin/items/purchase_request.html', item=item_shop, user=user,
                               purchase=item, current_user_role=current_user.role)
    elif not current_user.is_authenticated:
        return redirect('/login')



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
            photo = request.files['photo']

            razresh = photo.filename.split('.')[1]
            k = 1
            f = os.path.exists('static/images/items_images/' + str(k) + '.' + razresh)
            while f:
                k += 1
                f = os.path.exists('static/images/items_images/' + str(k) + '.' + razresh)
            fname = str(k) + '.' + razresh

            photo.save(os.path.join(app.config['FOLDER'], fname))

            session_db = db_session.create_session()
            new_item = Item_shop(name=name, description=description, count=count, price=price, photo=fname)
            session_db.add(new_item)
            session_db.commit()
            session_db.close()

            return redirect('/items')
        
    elif not current_user.is_authenticated:
        return redirect('/login')


@app.route('/items_users/<purchase_id>/can_be_recieved')
def can_be_recieved(purchase_id):
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        item = session_db.query(Item_user).filter_by(id=purchase_id).first()
        item.status = 'Ждёт вас'
        session_db.commit()
        session_db.close()
        return redirect('/')
    elif not current_user.is_authenticated:
        return redirect('/login')


@app.route('/items/<item_id>/delete', methods=['POST'])
def delete_item(item_id):
    if current_user.is_authenticated and current_user.role == 'Admin':
        session_db = db_session.create_session()
        item = session_db.query(Item_shop).filter_by(id=item_id).first()
        
        if item:
            item.is_archived = True
            session_db.commit()

        session_db.close()

        return render_template('admin/items/items_search')

    elif not current_user.is_authenticated:
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
            new_photo = request.files['photo']

            if new_name:
                item.name = new_name
            if new_description:
                item.description = new_description
            if new_count:
                item.count = new_count
            if new_price:
                item.price = new_price
            if new_photo:
                os.remove(app.config['FOLDER'] + '/' + item.photo)

                new_photo.save(os.path.join(app.config['FOLDER'], item.photo))

            session_db.commit()
            return redirect(f'/items')

    elif not current_user.is_authenticated:
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

        return render_template('teacher/class.html', **context, role=current_user.role)

    elif not current_user.is_authenticated:
        return redirect('/login')


@app.route('/classes/<class_name>')
def show_class(class_name):
    if current_user.is_authenticated and current_user.role == 'Teacher':
        classes = current_user.userclass.split(' ')
        session_db = db_session.create_session()
        students = session_db.query(User).filter_by(userclass=class_name).all()
        students_list = []
        for student in students:
            if student.id != current_user.id:
                student_data = {
                    'id': student.id,
                    'username': student.username,
                    'usersurname': student.usersurname,
                    'userotchestvo': student.userotchestvo,
                    'userbalance': student.userbalance,
                    'userclass': student.userclass
                }
                students_list.append(student_data)
        session_db.close()
        context = {'current_user_role': current_user.role,
                   'classes': classes,
                   'userbalance': current_user.userbalance,
                   'teacherid': current_user.id,
                   'students': students_list}

        return render_template('teacher/class.html', **context, role=current_user.role)

    elif not current_user.is_authenticated:
        return redirect('/login')


@app.route('/classes/<class_name>/<user_id>', methods=['GET', 'POST'])
def student_page(class_name, user_id):
    if current_user.is_authenticated and current_user.role == 'Teacher':
        if user_id:
            session_db = db_session.create_session()
            student = session_db.query(User).filter_by(id=user_id).first()
            teacher = session_db.query(User).filter_by(id=current_user.id).first()

            if request.method == 'POST':
                coins_amount = int(request.form.get('coins_amount', 0))
                action = request.form.get('action')

                if action == 'Выдать':
                    if coins_amount <= int(teacher.userbalance):
                        student.userbalance = str(int(student.userbalance) + coins_amount)
                        teacher.userbalance = str(int(teacher.userbalance) - coins_amount)
                        session_db.commit()

                elif action == 'Отнять':
                    if coins_amount <= int(student.userbalance):
                        student.userbalance = str(int(student.userbalance) - coins_amount)
                        teacher.userbalance = str(int(teacher.userbalance) + coins_amount)
                        session_db.commit()


            username = student.username
            usersurname = student.usersurname
            userotchestvo = student.userotchestvo
            userclass = student.userclass
            userbalance = student.userbalance
            teacherbalance = teacher.userbalance
            session_db.close()

            return render_template('teacher/student.html',
                                   username=username,
                                   usersurname=usersurname,
                                   userotchestvo=userotchestvo,
                                   userclass=userclass,
                                   userbalance=teacherbalance,
                                   studbalance=userbalance,
                                   user_id=user_id,
                                   current_user_role=current_user.role)

        return redirect(url_for('index'))
    elif not current_user.is_authenticated:
        return redirect(url_for('login'))


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

            if current_user.role == 'Student':
                return redirect('/')
            elif current_user.role == 'Teacher':
                return redirect('/classes')
            elif current_user.role == 'Admin':
                return redirect('/users')

        elif not all([login, password]):
            session_db.close()
            return render_template('authorization/login.html')

        else:
            session_db.close()
            return render_template('authorization/login.html')


@app.route('/logout', methods=['GET'])
def logout():
    if current_user.is_authenticated:
        logout_user()
        
        return redirect('/login')

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
    
    elif not current_user.is_authenticated:
        return redirect('/login')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)