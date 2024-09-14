# import flask for basic layout rendering and creating url
from flask import (
    Flask,
    render_template,
    flash,
    request,
    redirect,
    url_for,
    send_from_directory,
)

# CSRFProtect(app) will automatically generate a CSRF token for each form that is rendered by your Flask application. This token is a unique value associated with the user’s session. CSRFProtect provides a straightforward way to implement CSRF protection in a Flask application, ensuring that your forms are secure and that users are protected from common web security vulnerabilities.
from flask_wtf.csrf import CSRFProtect


# For security of user password, used hashed function and for login compare will in btw hash
from werkzeug.security import generate_password_hash, check_password_hash

# Creating login and logout and managing the user's session from database
from flask_login import (
    LoginManager,
    UserMixin,
    login_required,
    logout_user,
    login_user,
    current_user,
)

# Importing flask form to create form
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo

# Bootsrap class for app
from flask_bootstrap import Bootstrap5

# ORM mapping using Sqlalchemy
from flask_sqlalchemy import SQLAlchemy

# Sending mail using smtplib
from smtplib import SMTP

# import secret keys/password/mail from other files
from secret_tools import (
    SECRET_KEY,
    MY_MAIL,
    MY_PASS,
    DATABASE_URI,
    schooling,
    college,
    skills,
    projects,
)

# app configuring
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Correct key name
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
Bootstrap5(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"  # Redirect unauthenticated users to the login page


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Contact database tabel
class ContactDetails(db.Model):
    __tablename__ = "ContactedPeople"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ContactDetails (id={self.id}, name={self.name}, email={self.email}, subject={self.subject}, description={self.description})>"


# users database table
class Users(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)


# Form for user to contact me
class ContactForm(FlaskForm):
    name = StringField(
        "Enter Your Name.",
        validators=[DataRequired()],
        render_kw={"placeholder": "Type your name here", "class": "form-control"},
    )
    email = EmailField(
        "Enter Email Address.",
        validators=[DataRequired()],
        render_kw={"placeholder": "Your email"},
    )
    subject = StringField(
        "Subject.",
        validators=[DataRequired()],
        render_kw={"placeholder": "Title! Why you are trying to contact me?"},
    )
    description = TextAreaField(
        "Description.",
        render_kw={"placeholder": "What's going on in your mind?"},
    )
    submit = SubmitField("Send", render_kw={"class": "btn btn-success"})


# Form for sign up (new user)
class SignUpForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired(), Length(min=4, max=30)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )


# Form for login (existing user in database)
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


# take a message & email, send the message to the email
def send_email(message, email):
    with SMTP("smtp.gmail.com", port=587) as connection:
        connection.starttls()
        connection.login(MY_MAIL, MY_PASS)
        connection.sendmail(from_addr=email, to_addrs=MY_MAIL, msg=message)


# to show homepage
@app.route("/")
def home():
    return render_template("index.html")


# to show about page
@app.route("/about")
def about():
    return render_template("about.html")


# to send contact details or get the contact page
@app.route("/contact", methods=["GET", "POST"])
def contact():
    contact_form = ContactForm()
    if contact_form.validate_on_submit():
        # create a row of data entered by user to contact form
        row = ContactDetails(
            name=contact_form.name.data,
            email=contact_form.email.data,
            subject=contact_form.subject.data,
            description=contact_form.description.data,
        )
        try:
            # put the row inside database table named class "ContactDetails"
            db.session.add(row)
            db.session.commit()  # commit to add
            flash("Message sent successfully!", "success")
        except Exception as e:
            # if any reason not commited then roll back to previous state
            db.session.rollback()

            # if any error occurs then send error message to own email
            message = f"Subject: {contact_form.name.data}\n\nEmail: {contact_form.email.data}\nSubject: {contact_form.subject.data}\nUser Description: {contact_form.description.data}\nTrying to send the contact details but {e} occurs."
            send_email(message=message, email=contact_form.email.data)

            # give user to error message
            flash(f"An error occurred: {e}", "error")

    return render_template("contact.html", contact_form=contact_form)


# to show my resume
@app.route("/resume")
def resume():
    return render_template(
        "resume.html",
        schooling=schooling,
        college=college,
        projects=projects,
        skills=skills,
    )


# route for new user to signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    signup_form = SignUpForm()
    if signup_form.validate_on_submit():
        # hashing and salting the password entered by user
        hashed_password = generate_password_hash(
            password=signup_form.password.data, salt_length=10, method="pbkdf2:sha256"
        )
        # creating new user
        new_user = Users(
            username=signup_form.username.data,
            email=signup_form.email.data,
            password_hash=hashed_password,
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully! ", "success")

            # if user signed in then show a basic landing page
            return redirect(
                url_for(
                    "landing",
                    user=new_user.username,
                    welcome_message="Welcome",
                    action="signing up",
                )
            )
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")

    # for get method
    return render_template("signup.html", form=signup_form)


# route for user to login
@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data

        # fetch the user by filtering on the basis of email (because emails are unique)
        user = Users.query.filter_by(email=email).first()

        # compare if user found and the password entered by user is equal to the hashed password for user inside Users
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(
                url_for(
                    "landing",
                    user=user.username,
                    welcome_message="Welcome Back",
                    action="login",
                )
            )
        else:
            flash("Invalid email or password.", "error")

    return render_template("login.html", form=login_form)


# route to landing page
@app.route("/landing")
@login_required
def landing():
    # check the route if user lands from the login then landing_page.html in some manner and if user lands from signup route the different manner
    user = request.args.get("user", default=current_user.username)
    welcome_message = request.args.get("welcome_message", default="Welcome")
    action = request.args.get("action", default="visiting")
    return render_template(
        "landing.html", user=user, welcome_message=welcome_message, action=action
    )


# route for logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/pending")
def pending():
    return render_template("pending.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
