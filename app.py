from flask import Flask, render_template, request, jsonify
import requests
from account_creator import AccountCreator
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)

PROXY_CONFIG = {
    'host': 'proxy.toolip.io',
    'port': '31113',
    'username': 'tl-729495ab273e521d4bb30c78ef1d776c91ebf647059038319f2caac13ec7afea-country-us-session-5153a',
    'password': 'tnuo71dl6g9p'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_account', methods=['POST'])
def create_account():
    try:
        # 10minutemail API'den geçici mail al
        temp_mail_response = requests.get('https://10minutemail.com/api/v1/email')
        if temp_mail_response.status_code == 200:
            email = temp_mail_response.json().get('email')
        else:
            return jsonify({'error': 'Geçici mail alınamadı'}), 400

        creator = AccountCreator(
            proxy_host=PROXY_CONFIG['host'],
            proxy_port=PROXY_CONFIG['port'],
            proxy_username=PROXY_CONFIG['username'],
            proxy_password=PROXY_CONFIG['password']
        )
        
        result = creator.create_account(email=email)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 