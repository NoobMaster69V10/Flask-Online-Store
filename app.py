import os
from flask import Flask, request, render_template, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, Length, ValidationError
from wtforms import FileField, SubmitField, StringField, FloatField, PasswordField, validators
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_bcrypt import Bcrypt

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/files'
app.config['SECRET_KEY'] = 'supersecretkey'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password
        }


# Post Form
class PostForm(FlaskForm):
    name = StringField("name", validators=[validators.DataRequired(), validators.Length(min=3, max=100)])
    price = FloatField("price", validators=[validators.DataRequired()])
    description = StringField("description", validators=[validators.DataRequired()])
    category = StringField("category", validators=[validators.DataRequired(), validators.Length(min=3, max=100)])
    file = FileField("file")
    submit = SubmitField("Upload")


# Post db model
class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    description = db.Column(db.String)
    category = db.Column(db.String(100))
    filename = db.Column(db.String)

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user,
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'category': self.category,
            'filename': self.filename
        }


# Register Form
class RegisterForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


# Login Form
class LoginForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(f'/profile/{form.username.data}')
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


search_result = []
search_word = []


@app.route('/')
def show_all():
    data = [post.to_dict() for post in Post.query.all()]
    category_lst = []
    category_lst.clear()
    for e in data:
        category_lst.append(e['category'])
    category_lst = list(set(category_lst))
    search_result.clear()
    search_word.clear()
    return render_template('all_posts.html', data=data, category_lst=category_lst)


@app.route('/all/order/<string:direct>')
def all_order(direct):
    data = [post.to_dict() for post in Post.query.all()]
    ordered_data = None
    category_lst = []
    category_lst.clear()
    for e in data:
        category_lst.append(e['category'])
    category_lst = list(set(category_lst))
    if direct == 'down':
        ordered_data = [post.to_dict() for post in Post.query.order_by(Post.price.desc())]
    elif direct == 'up':
        ordered_data = [post.to_dict() for post in Post.query.order_by(Post.price.asc())]
    return render_template('sorted_posts.html', ordered_data=ordered_data, category_lst=category_lst,
                           title='All products',
                           link_up='/all/order/up', link_down='/all/order/down')


@app.route('/profile/<string:user>')
@login_required
def profile(user):
    info = Post.query.filter(Post.user == user).all()
    return render_template('profile.html', info=info, user=user)


@app.route('/new')
def new_products():
    data = [post.to_dict() for post in Post.query.all()]
    ordered_data = [post.to_dict() for post in Post.query.order_by(Post.id.desc())]
    category_lst = []
    category_lst.clear()
    for e in data:
        category_lst.append(e['category'])
    category_lst = list(set(category_lst))
    search_result.clear()
    search_word.clear()
    return render_template('new_posts.html', ordered_data=ordered_data, category_lst=category_lst)


with app.app_context():
    db.create_all()
    app.run()
