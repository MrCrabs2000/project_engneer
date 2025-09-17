from flask import Flask, request, render_template
from tgbotiha import check_response


app = Flask(__name__)
app.config['TELEGRAM_BOT_TOKEN'] = '8373230853:AAExLeEupdgJyfOZV7o3GtUEiAQZxlWVMr0'


@app.route('/')
def index():
    return render_template('ind.html')


@app.route('/register')
def login():
    return render_template('register.html')


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
    if check_response(app, data):
        return data
    else:
        return 'Authorization failed'


if __name__ == "__main__":

    app.run(host='0.0.0.0', port=8000, debug=True)
