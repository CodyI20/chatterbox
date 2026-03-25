from waitress import serve
from chatterbox_serverUpgraded import app

if __name__ == '__main__':
    print("Starting production server on http://10.38.94.252:5000...")
    serve(app, host='10.38.94.252', port=5000, threads=4)
