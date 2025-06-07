from flask import Flask, render_template, url_for, request, redirect, session, send_file, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_admin import Admin, expose
from flask_login import current_user
from flask_admin.contrib.sqla import ModelView
from models import *
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import timedelta
import os
import secrets
import logging


UPLOAD_DIRECTORY = 'users'
DATABASE_PATH = 'site.db'


def create_user_folder(username):
    user_folder = os.path.join(UPLOAD_DIRECTORY, f'{username}')
    os.makedirs(user_folder, exist_ok=True)
    return user_folder


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True
app.secret_key = secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(hours=720)

socketio = SocketIO(app, cors_allowed_origins="*")

db.init_app(app)

with app.app_context():
    db.create_all()


# ADMIN PANEL SET UP (NEEDS TO BE SECURED)
class SecureModelView(ModelView):
    def is_accessible(self):
        if 'user_id' not in session:
            return False
        admin_record = Admin_Table.query.filter_by(user_id=session['user_id'])
        return admin_record is not None

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login_user'))

admin = Admin(app, name='Admin Panel')
admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Post, db.session))
admin.add_view(SecureModelView(Reply, db.session))
admin.add_view(SecureModelView(Link, db.session))
admin.add_view(SecureModelView(File, db.session))
admin.add_view(SecureModelView(Admin_Table, db.session))

# INDEX ENDPOINT
@app.route("/")
def index_page():

    users = User.query.all()
    user_count = len(users)
    page = request.args.get("page", 1, type=int)
    per_page = 5
    posts = Post.query.order_by(Post.id.desc()).paginate(page=page, per_page=per_page)
    files = File.query.filter_by(private=False)
    files = files[::-1]
    replies = Reply.query.all()
    is_admin = False
    if 'user_id' in session:
        admins = Admin_Table.query.filter_by(user_id=session['user_id']).first()
        current_user = User.query.filter_by(id=session['user_id']).first()
        if admins:
            is_admin = True
        return render_template('logged_in/index.html', username=session['username'], users=users, files=files, posts=posts, replies=replies, user_count=user_count, cur_user=current_user, is_admin=is_admin)
    else:
        return render_template("logged_out/index.html", users=users, files=files, posts=posts, replies=replies, user_count=user_count)


# APPLICATION ENDPOINT
@app.route("/apply", methods=['GET','POST'])
def application():

    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if (" " in username) or (" " in password) or (" " in email):
            return render_template('logged_out/register.html', error="No spaces allowed.")
        hashed_password = generate_password_hash(password)

        if not User.query.filter((User.username == username) | (User.email == email)).first():
            user_application = Queue(username=username, email=email, password=hashed_password)
            db.session.add(user_application)
            db.session.commit()
            create_user_folder(username)
            return redirect(url_for('login_user'))
        else:
            return render_template("logged_out/register.html", error="Username or Email already in use.")


    if request.method == 'GET':
        return render_template("logged_out/register.html")

queue = Blueprint('queue', __name__, url_prefix='/admin/queue')
@queue.route('/all', methods=['GET'])
def show_queue():
    try:
        admin_auth = Admin_Table.query.filter_by(user_id=session['user_id']).first()
        if not admin_auth:
            return render_template('404.html')
        queue_list = Queue.query.all()
        # PARSE WITH JIRA
        return render_template('logged_in/queue.html', users=queue_list)

    except:
        return render_template('404.html')

@queue.route('/accept/<int:id>', methods=['GET', 'POST'])
def accept_user(id):
    try:
        queue_list = Queue.query.all()
        user_to_accept = Queue.query.filter_by(id=id).first()
        if not user_to_accept:
            return render_template('404.html')
        new_user = User(username=user_to_accept.username, password=user_to_accept.password, email=user_to_accept.email)
        db.session.add(new_user)
        db.session.delete(user_to_accept)
        db.session.commit()
        return redirect(url_for("queue.show_queue"))
    except:
        return render_template('404.html')

app.register_blueprint(queue)

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
            current_user = User.query.filter_by(id=session['user_id']).first()
            return render_template('logged_in/login.html', accept= "Success!", username=session['username'],cur_user=current_user)
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
            current_user = User.query.filter_by(id=session['user_id']).first()
            return render_template('logged_in/upload.html', username=session['username'], cur_user=current_user)
        else:
            return redirect(url_for('login_user'))

    if request.method == 'POST' and ('user_id' in session):
        if 'file' not in request.files:
            current_user = User.query.filter_by(id=session['user_id']).first()
            return render_template('logged_in/upload.html', error="Select a file", cur_user=current_user)

        uploaded_file = request.files['file']
        try:
            private = request.form['private']

            if private == 'on':
                private = True
            else:
                private = False
        except:
            private = False
        print(private)
        if uploaded_file.filename == '':
            current_user = User.query.filter_by(id=session['user_id']).first()
            return render_template('logged_in/upload.html', error='No file selected', username=session['username'], cur_user=current_user)
        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            upload_folder = f'users/{session["username"]}'
            filepath = upload_folder + '/' + filename
            uploaded_file.save(filepath)
            user_id = session['user_id']
            username = session['username']
            file_to_upload = File(filename=filename, filepath=filepath, user_id=user_id, username=username, private=private)
            db.session.add(file_to_upload)
            db.session.commit()
            current_user = User.query.filter_by(id=session['user_id']).first()
            return render_template('logged_in/upload.html', accept='File uploaded', username=session['username'],cur_user=current_user)
        return render_template('404.html')

# PROFILE ENDPOINT
@app.route('/profile', methods=['GET'])
def profile():
    if 'user_id' in session:
        current_user = User.query.filter_by(id=session['user_id']).first()
        page = request.args.get("page", 1, type=int)
        per_page = 5
        posts = Post.query.filter_by(user_id=session['user_id']).order_by(Post.id.desc()).paginate(page=page, per_page=per_page)
        replies = Reply.query.all()
        files = File.query.filter_by(user_id=session['user_id']).all()
        user_id = session['user_id']
        user = User.query.filter_by(id=user_id).first()
        return render_template('logged_in/profile_external.html', username=session['username'], files=files, user_id=user_id, user=user,posts=posts,replies=replies, cur_user=current_user)
    else:
        return redirect(url_for('login_user'))


@app.route('/profile/<username>', methods=['GET'])
def profile_external(username):
    if 'user_id' in session:
        page = request.args.get("page", 1, type=int)
        current_user = User.query.filter_by(id=session['user_id']).first()
        per_page = 5
        replies = Reply.query.all()
        user = User.query.filter_by(username=username).first()
        files = File.query.filter_by(username=username, private = False)
        files = files[::-1]
        posts = Post.query.filter_by(user_id=user.id).order_by(Post.id.desc()).paginate(page=page, per_page=per_page)

        return render_template('logged_in/profile_external.html', username=session['username'], files=files, user_id=user.id, user=user, posts=posts, replies=replies, cur_user=current_user)
    else:
        return redirect(url_for('login_user'))


# SETTINGS ENDPOINT
@app.route('/settings', methods=['GET'])
def settings():
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
        return redirect(url_for('login_user'))


@app.route('/file/delete/<int:id>', methods=['POST'])
def delete_file(id):
    if 'user_id' in session:
        try:
            file_to_delete = File.query.filter_by(id=id).first()
            if file_to_delete.user_id == session['user_id']:
                db.session.delete(file_to_delete)
                db.session.commit()
                return redirect(url_for('settings'))
        except:
            return redirect(url_for('settings'))


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
            return redirect(url_for('settings'))
        return render_template('404.html')
    else:
        return render_template('404.html')


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
        return redirect(url_for('login_user'))


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
        return redirect(url_for('login_user'))


create_admin = Blueprint('create_admin', __name__, url_prefix='/admin/create')

@create_admin.before_request
def before_request():
    logging.info("Attempt to create admin.")



@create_admin.after_request
def after_request(response):
    if 'user_id' in session:
        logging.info(f'User {session["username"]} created an admin.')
    return response


@create_admin.route('/<int:id>', methods=['GET'])
def make_admin(id):
    HEAD_ADMIN = ['mode']
    if 'user_id' in session:
        if session['username'] in HEAD_ADMIN:
            username = User.query.filter_by(id=id).first()
            username = username.username
            new_admin = Admin_Table(user_id=id, added_by=session['user_id'], username=username)
            db.session.add(new_admin)
            db.session.commit()
            return redirect(url_for('index_page'))
        else:
            return redirect(url_for('index_page'))
    else:
        return redirect(url_for('index_page'))

app.register_blueprint(create_admin)

bioAPI = Blueprint('bioAPI', __name__, url_prefix="/api/bio")
@bioAPI.route('/user/<int:id>', methods=['GET'])
def get_bio(id):
    try:
        bio = Bio.query.filter_by(user_id=id).first()
        return jsonify(bio.to_dict())
    except:
        return render_template('404.html')

app.register_blueprint(bioAPI)





# ACTIVE USER COUNT
active_users = 0


@socketio.on('connect')
def handle_connect():
    global active_users
    active_users += 1
    socketio.emit('update_count', {'count': active_users})


@socketio.on('disconnect')
def handle_disconnect():
    global active_users
    active_users -= 1
    socketio.emit('update_count', {'count': active_users})


if __name__ == "__main__":

    app.run(debug=True)
