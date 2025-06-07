from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)

    profile_picture = db.Column(db.String(200), nullable=False, default='./static/default.jpeg')
    color = db.Column(db.String(10), nullable=False, default="#FFFFFF")
    text_color = db.Column(db.String(10), nullable=False, default="#FFFFFF")
    card_color = db.Column(db.String(10), nullable=False, default='#1E1E1E')

    posts = db.relationship('Post', backref='author', lazy=True)
    files = db.relationship('File', backref='user', lazy=True)

class Admin_Table(db.Model):
    __tablename__ = 'admins'
    admin_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    added_by = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(120), nullable=False)

class Link(db.Model):
    __tablename__ = 'links'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Post(db.Model):  # changed from Posts → Post
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # changed from Integer to Text
    username = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # this links post to user
    replies = db.relationship('Reply', backref='post', cascade='all, delete-orphan', passive_deletes=True)


class Reply(db.Model):
    __tablename__ = 'reply'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.Text, nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    upload_time = db.Column(db.DateTime, server_default=db.func.now())
    username = db.Column(db.String(50), nullable=False)
    private = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Queue(db.Model):
    __tablename__ = 'queues'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)

    profile_picture = db.Column(db.String(200), nullable=False, default='./static/default.jpeg')
    color = db.Column(db.String(10), nullable=False, default="#FFFFFF")
    text_color = db.Column(db.String(10), nullable=False, default="#FFFFFF")
    card_color = db.Column(db.String(10), nullable=False, default='#1E1E1E')

    def to_dict(self):
        return {
            'username': self.username,
            'email': self.email,
            'id': self.id
        }

class Bio(db.Model):
    __tablename__ = 'Bios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    discord = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), nullable=False, default="#FFFFFF")
    background = db.Column(db.Text, nullable=False, default= "#000000")
    primary_color = db.Column(db.Text, nullable=False, default="#FFFFFF")
    steam = db.Column(db.Text, nullable=True)
    github = db.Column(db.Text, nullable=True)
    banner = db.Column(db.Text, nullable=True)
    anime_list = db.Column(db.Text, nullable=True)
    link = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True, default="")
    views = db.Column(db.Text, nullable=False, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'discord': self.discord,
            'description': self.description,
            'color': self.color,
            'background': self.background,
            'primary': self.primary_color,
            'tags': self.tags,
            'steam': self.steam,
            'github': self.github,
            'anime_list': self.anime_list,
            'banner': self.banner,
            'link': self.link,
            'views': self.views
        }
