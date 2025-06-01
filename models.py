from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    profile_picture = db.Column(db.String(200), nullable=False, default='./static/default.jpeg')
    color = db.Column(db.String(10), nullable=False, default='#FFFFFF')
    text_color = db.Column(db.String(10), nullable=False, default='#FFFFFF')
    card_color = db.Column(db.String(10), nullable=False, default='#1E1E1E')
    admin = db.Column(db.Boolean(), nullable=False, default=False)
    sparkle = db.Column(db.Text, nullable=True, default='./static/yellow.gif')
    posts = db.relationship('Post', backref='author', lazy=True)
    files = db.relationship('File', backref='user', lazy=True)


class Post(db.Model):  # changed from Posts → Post
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # changed from Integer to Text
    username = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # this links post to user


class Reply(db.Model):
    __tablename__ = 'reply'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.Text, nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    upload_time = db.Column(db.DateTime, server_default=db.func.now())
    username = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
