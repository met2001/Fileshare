from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Association table for many-to-many: MalwareSamples <-> Tags
sample_tags = db.Table(
    'sample_tags',
    db.Column('sample_id', db.Integer, db.ForeignKey('malware_samples.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    plan = db.Column(db.String(20), default='free')  # 'free', 'pro', etc.
    upload_quota = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    files = db.relationship('File', backref='uploader', lazy=True)
    writeups = db.relationship('Writeup', backref='author', lazy=True)
    downloads = db.relationship('Download', backref='user', lazy=True)

class File(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    sha256 = db.Column(db.String(64), unique=True, nullable=False)
    sha1 = db.Column(db.String(40))
    md5 = db.Column(db.String(32))
    filesize = db.Column(db.BigInteger)
    mime_type = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_malicious = db.Column(db.Boolean, default=False)
    download_enabled = db.Column(db.Boolean, default=False)

    malware_sample = db.relationship('MalwareSample', backref='file', uselist=False)
    downloads = db.relationship('Download', backref='file', lazy=True)


class MalwareSample(db.Model):
    __tablename__ = 'malware_samples'

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), unique=True, nullable=False)
    family = db.Column(db.String(100), nullable=True)
    behavior_summary = db.Column(db.Text, nullable=True)
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    published = db.Column(db.Boolean, default=True)

    writeups = db.relationship('Writeup', backref='sample', lazy=True)
    tags = db.relationship('Tag', secondary=sample_tags, back_populates='samples')

class Writeup(db.Model):
    __tablename__ = 'writeups'

    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.Integer, db.ForeignKey('malware_samples.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Markdown or HTML
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    samples = db.relationship('MalwareSample', secondary=sample_tags, back_populates='tags')

class Download(db.Model):
    __tablename__ = 'downloads'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    download_time = db.Column(db.DateTime, default=datetime.utcnow)
