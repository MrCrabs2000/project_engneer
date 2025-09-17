import hmac
import hashlib


def check_response(app, data):
    d = data.copy()
    del d['hash']
    d_list = []
    for key in sorted(d.keys()):
        if d[key] != None:
            d_list.append(key + '=' + d[key])
    data_string = bytes('\n'.join(d_list), 'utf-8')

    secret_key = hashlib.sha256(app.config['TELEGRAM_BOT_TOKEN'].encode('utf-8')).digest()
    hmac_string = hmac.new(secret_key, data_string, hashlib.sha256).hexdigest()
    if hmac_string == data['hash']:
        return True

    return False
