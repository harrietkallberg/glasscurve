import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <h1>🔥 Glass Firing Curve Generator</h1>
    <p>Hello from Railway! The app is working!</p>
    <p>Your Flask app is successfully deployed.</p>
    '''

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'app': 'Glass Firing Curve Generator'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)