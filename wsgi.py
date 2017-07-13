# Run a test server.
from runestone import create_app, db
import os

app = create_app(os.getenv('FLASK_CONFIG') or 'default')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
