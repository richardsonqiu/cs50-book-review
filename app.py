import os, json

from flask import Flask, request, session, redirect, render_template, jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

app = Flask(__name__)

# API
KEY = "DGvjXcAUMWcpmQ80eRrbA"
API_URL = "https://www.goodreads.com/book/"
# res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "KEY", "isbns": "9781632168146"})
# print(res.json())

# # Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine('postgres://xtafrcfepfrhkv:1da5e6972ef6a58f22c55d716ca79ad297a6d7eefd350d633aacf8de4c636fa5@ec2-50-17-21-170.compute-1.amazonaws.com:5432/da6g2ambslb4rn')
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
# @login_required
def index():
    """ Show search library """
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """ Log user in """

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return render_template("error.html", message="please provide username")
        password = request.form.get("password")
        if not password:
            return render_template("error.html", message="please provide password")
        
        rows = db.execute("SELECT * FROM users WHERE username=:username", {"username": username})

        # check username exists and password correct

        # remember which user has logged in 

        # redirect user to home page again

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """ Log user out """
    session.clear();
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """ Register user """
    if request.method == "GET":
        return render_template("register.html")
    else:
        # Check username submitted
        username = request.form.get("username")
        if not username:
            return render_template("error.html", message="please provide username")
        
        # Check if username already exists
        username_check = db.execute("SELECT * FROM users WHERE username=:username", {"username": username}).fetchone()
        if username_check != 1:
            return render_template("error.html", message="username already exists")

        # Check password submitted
        password = request.form.get("password")
        if not password:
            return render_template("error.html", message="please provide password")

        # Check confirmation password submitted
        confirm_password = request.form.get("confirm_password")
        if not confirm_password:
            return render_template("error.html", message="please provide confirmation password")

        # Check passwords are equal
        if not password == confirm_password:
            return render_template("error.html", message="passwords did not match")
        
        # Hash password to store in DB
        hashedPassword = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        # Insert registered user into DB
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)", {"username": username, "password": hashedPassword})

        db.commit()

        flash("Account created", 'info')

        return redirect("/login")

@app.route("/search", methods=["GET"])
@login_required
def search():
    """ Search books """ 

if __name__ == "__main__":
    app.run(debug=True)