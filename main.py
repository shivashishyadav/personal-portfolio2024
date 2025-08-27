# import flask for basic layout rendering and creating url
from flask import (
    Flask,
    render_template,
    flash,
)

# CSRFProtect(app) will automatically generate a CSRF token for each form that is rendered by your Flask application. This token is a unique value associated with the user’s session. CSRFProtect provides a straightforward way to implement CSRF protection in a Flask application, ensuring that your forms are secure and that users are protected from common web security vulnerabilities.
from flask_wtf.csrf import CSRFProtect

from dotenv import load_dotenv
import os

# Importing flask form to create form
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo

# Bootsrap class for app
from flask_bootstrap import Bootstrap5

# Sending mail using smtplib
from smtplib import SMTP

# import secret keys/password/mail from other files
from myinfo import (
    schooling,
    college,
    skills,
    projects,
)

# Load environment variables from .env file
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
MY_MAIL = os.getenv("MY_MAIL")
MY_PASS = os.getenv("MY_PASS")

# app configuring
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# Correct key name
csrf = CSRFProtect(app)
Bootstrap5(app)

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
    message = f"Subject: {contact_form.name.data}\n\nEmail: {contact_form.email.data}\nSubject: {contact_form.subject.data}\nUser Description: {contact_form.description.data}."

    if contact_form.validate_on_submit():
        try:
            flash("Message sent successfully!", "success")
            send_email(message=message, email=contact_form.email.data)

        except Exception as e:
            # if any reason not commited then roll back to previous state

            # if any error occurs then send error message to own email
            error_message = (
                message + f"\nTrying to send the contact details but {e} occurs."
            )
            send_email(message=error_message, email=contact_form.email.data)

            # give user to error message
            flash("An error occurred, Try again", "danger")

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

@app.route("/pending")
def pending():
    return render_template("pending.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
