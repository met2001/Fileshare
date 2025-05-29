from flask import Flask, render_template, url_for, request, redirect, session, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import *
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import timedelta
import os
import secrets


UPLOAD_DIRECTORY = 'users'
DATABASE_PATH = 'site.db'


def create_user_folder(username):
    user_folder = os.path.join(UPLOAD_DIRECTORY, f'{username}')
    os.makedirs(user_folder, exist_ok=True)
    return user_folder


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True
app.secret_key = secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(hours=720)


db.init_app(app)

with app.app_context():
    db.create_all()


# ADMIN PANEL SET UP (NEEDS TO BE SECURED)
admin = Admin(app, name='Admin Panel')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Post, db.session))
admin.add_view(ModelView(File, db.session))

# INDEX ENDPOINT
@app.route("/")
def index_page():
    users = User.query.all()
    if 'user_id' in session:
        page = request.args.get("page", 1, type=int)
        per_page = 5
        posts = Post.query.order_by(Post.id.desc()).paginate(page=page, per_page=per_page)
        files = File.query.all()
        replies = Reply.query.all()
        return render_template('logged_in/index.html', username=session['username'], users=users, files=files, posts=posts, replies=replies)
    else:
        return render_template("logged_out/index.html", users=users)


# REGISTER ENDPOINT
@app.route("/register", methods=['GET','POST'])
def register_user():

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        if not User.query.filter((User.username == username) | (User.email == email)).first():
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            create_user_folder(username)
            return redirect(url_for('login_user'))
        else:
            return render_template("logged_out/register.html", error="Username or Email already in use.")


    if request.method == 'GET':
        return render_template("logged_out/register.html")


# LOGIN ENDPOINT
@app.route("/login", methods=['GET','POST'])
def login_user():
    if request.method == 'POST':
        # LOGIN/SESSION LOGIC HERE
        username = request.form['username']
        password = request.form['password']
        # CHECK IF CREDS MATCH IN DATABASE
        user = User.query.filter_by(username=username).first()
        email_user = User.query.filter_by(email=username).first()
        if (user and check_password_hash(user.password, password)) or (email_user and check_password_hash(email_user.password, password)):
            # SESSION LOGIC HERE
            if email_user:
                session['user_id'] = email_user.id
                session['username'] = email_user.username
            if user:
                session['user_id'] = user.id
                session['username'] = user.username
            #return redirect(url_for(f'/user/{username}')) # NEED TO SET UP ENDPOINT
            return render_template('logged_in/login.html', accept= "Logged In", username=session['username'])
        else:
            return render_template('logged_out/login.html', error="Usename/Email or Password are invalid.")

    if request.method == 'GET':
        return render_template('logged_out/login.html')
    else:
        return render_template('404.html')


# LOGOUT ENDPOINT
@app.route("/logout", methods=['GET'])
def logout():
    if request.method == 'GET':
        if 'user_id' in session:
            session.clear()
            return redirect(url_for('index_page'))
        else:
            return redirect(url_for('index_page'))


# UPLOAD ENDPOINT
@app.route("/upload", methods=['GET','POST'])
def upload():
    if request.method == 'GET':
        if 'user_id' in session:
            return render_template('logged_in/upload.html', username=session['username'])
        else:
            return redirect(url_for('index_page'))

    if request.method == 'POST' and ('user_id' in session):
        if 'file' not in request.files:
            return render_template('logged_in/upload.html', error="Select a file")

        uploaded_file = request.files['file']

        if uploaded_file.filename == '':
            return render_template('logged_in/upload.html', error='No file selected', username=session['username'])
        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            upload_folder = f'users/{session["username"]}'
            filepath = upload_folder + '/' + filename
            uploaded_file.save(filepath)
            user_id = session['user_id']
            username = session['username']
            file_to_upload = File(filename=filename, filepath=filepath, user_id=user_id, username=username)
            db.session.add(file_to_upload)
            db.session.commit()
            return render_template('logged_in/upload.html', accept='File uploaded', username=session['username'])
        return render_template('404.html')

# PROFILE ENDPOINT
@app.route('/profile', methods=['GET'])
def profile():
    if 'user_id' in session:
        page = request.args.get("page", 1, type=int)
        per_page = 5
        posts = Post.query.filter_by(user_id=session['user_id']).order_by(Post.id.desc()).paginate(page=page, per_page=per_page)
        replies = Reply.query.all()
        files = File.query.filter_by(user_id=session['user_id']).all()
        user_id = session['user_id']
        user = User.query.filter_by(id=user_id).first()
        return render_template('logged_in/profile.html', username=session['username'], files=files, user_id=user_id, user=user,posts=posts,replies=replies)
    else:
        return render_template('404.html')


@app.route('/profile/<username>', methods=['GET'])
def profile_external(username):
    if 'user_id' in session:
        page = request.args.get("page", 1, type=int)
        per_page = 5
        posts = Post.query.filter_by(user_id=session['user_id']).order_by(Post.id.desc()).paginate(page=page, per_page=per_page)
        replies = Reply.query.all()
        files = File.query.filter_by(user_id=session['user_id']).all()
        user = User.query.filter_by(username=username).first()
        if session['user_id'] == user.id:
            return redirect(url_for('profile'))

        return render_template('logged_in/profile_external.html', username=session['username'], files=user.files, user_id=user.id, user=user)
    else:
        return redirect(url_for('login_user'))
# DOWNLOAD ENDPOINT
@app.route('/download/<int:id>', methods=['GET'])
def download(id):
    file_record = File.query.filter_by(id=id).first()
    if 'user_id' in session and file_record:
        filepath = file_record.filepath
        filepath = os.path.abspath(filepath)
        filename = file_record.filename
        return send_file(filepath, as_attachment=True, download_name=filename)
    else:
        return render_template('404.html')


@app.route('/color/<int:id>', methods=['POST'])
def change_color(id):
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        if session['user_id'] == id:
            name_color = request.form['color']
            card_color = request.form['card_color']
            text_color = request.form['text_color']
            user.color = name_color
            user.card_color = card_color
            user.text_color = text_color
            db.session.commit()
            return redirect(url_for('profile'))
        return 'error with user session', 400
    else:
        return "error no login detected", 400


@app.route('/post', methods=['POST'])
def make_post():
    if 'user_id' in session:
        content = request.form['content']
        username = session['username']
        user_id = session['user_id']
        post = Post(content=content, username=username,user_id=user_id)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index_page'))
    else:
        return render_template('404.html')


@app.route('/reply/<int:id>',methods=['POST'])
def reply(id):
    if 'user_id' in session:
        post_id = id
        username = session['username']
        content = request.form['content']
        reply = Reply(post_id=post_id, username=username, content=content)
        db.session.add(reply)
        db.session.commit()
        return redirect(url_for('index_page'))
    else:
        return render_template('404.html')


if __name__ == "__main__":
    app.run(debug=True)
