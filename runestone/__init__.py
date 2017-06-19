from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
db = SQLAlchemy(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bmiller:@localhost/runestone'

from runestone.book_server.server import book_server

app.register_blueprint(book_server)
