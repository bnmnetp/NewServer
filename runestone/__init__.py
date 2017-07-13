from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://millbr02:@localhost/runestone'
db = SQLAlchemy(app)


from runestone.book_server.server import book_server

app.register_blueprint(book_server)
