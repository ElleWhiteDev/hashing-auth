from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, AddFeebackForm


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///hash_auth"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


toolbar = DebugToolbarExtension(app)

app.app_context().push()

connect_db(app)
db.create_all()


@app.route('/')
def home_page():
    return redirect('/register')

@app.route('/register', methods=["GET", "POST"])
def register_user():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken')
            return render_template('register.html', form=form)
        session['username'] = new_user.username
        flash(f"Welcome {new_user.first_name}! Account Creation Successful!", 'success')
        return redirect(f'/users/{username}')

    return render_template('register.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.first_name}!", 'info')
            session['username'] = user.username
            return redirect(f'/users/{username}')
        else:
            form.username.errors = ['Invalid username or password']

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_user():
    if 'username' in session:
        username = session['username']
        session.pop('username')
        flash('You have been logged out', 'info')
    else:
        flash('You are not logged in', 'warning')

    return redirect('/')



@app.route('/users/<username>')
def user_page(username):
    if username != session['username']:
        flash('Please login first', 'danger')
        return redirect('/login')

    user = User.query.get_or_404(username)
    feedback = Feedback.query.filter_by(username=username).all()
    print(feedback)
    return render_template("user_page.html", user=user, feedback=feedback)
    

@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    if username != session['username']:
        flash('Please login first', 'danger')
        return redirect('/login')
    
    user = User.query.get(username)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User Deleted", 'info')
    else:
        flash('User not found', 'danger')

    return redirect('/')


@app.route('/users/<username>/feedback/add', methods=["GET","POST"])
def add_feedback(username):
    if username != session['username']:
        flash('Please login first', 'danger')
        return redirect('/login')
    else:
        form = AddFeebackForm()
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data

            new_feedback = Feedback(title=title, content=content, username=username)
            db.session.add(new_feedback)
            db.session.commit()
            flash("Feedback Saved", 'success')
            return redirect(f"/users/{username}")

    return render_template('/add_feedback.html', form=form)


@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    username = feedback.user.username

    if username != session['username']:
        flash('Please login first', 'danger')
        return redirect('/login')

    form = AddFeebackForm(obj=feedback)
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()
        flash("Feedback Updated", 'success')
        return redirect(f"/users/{feedback.user.username}")

    return render_template('/add_feedback.html', form=form)


@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    username = feedback.user.username

    if username != session['username']:
        flash('Please login first', 'danger')
        return redirect('/login') 
    
    db.session.delete(feedback)
    db.session.commit()
    flash("Feedback Deleted", 'info')
    return redirect(f"/users/{feedback.user.username}")
