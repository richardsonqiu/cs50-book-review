import os, json, requests

from flask import Flask, request, session, redirect, render_template, jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
@login_required
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

        result = rows.fetchone()
        
        # check username exists and password correct
        if result == None or not check_password_hash(result[2], password):
            return render_template("error.html", message="invalid username and/or password")

        # remember which user has logged in 
        session["user_id"] = result[0]
        session["user_username"] = result[1] 
        print(result[0])
        print(result[1])

        # redirect user to home page again
        return redirect("/")
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
        if username_check:
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
        
        # Hash password to store in DB , method='pbkdf2:sha256', salt_length=8
        hashed_password = generate_password_hash(password)

        # Insert registered user into DB
        db.execute("INSERT INTO users (username, hashed_password) VALUES (:username, :hashed_password)", {"username": username, "hashed_password": hashed_password})

        db.commit()

        flash("Account created", 'info')

        return redirect("/login")

@app.route("/search", methods=["GET"])
@login_required
def search():
    """ Search books """ 
    search_book = request.args.get("search_book")
    if not search_book:
        return render_template("error.html", message="Please provide your desired search")

    query = "%" + search_book + "%"
    
    rows = db.execute("SELECT isbn, title, author, year FROM books WHERE (isbn LIKE :query) OR (title LIKE :query) OR (author LIKE :query)", {"query": query})

    if rows.rowcount == 0:
        return render_template("error.html", message="Sorry! Cannot find your desired book!")
    
    books = rows.fetchall()

    return render_template("results.html", books=books)

@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    """ GET BOOK PAGE """
    if request.method == "GET":
        rows = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn=:isbn", {"isbn": isbn})

        bookDetails = rows.fetchall()

        """ GOODREADS review """
        
        # Read Api key from env 
        key = os.getenv("GOODREADS_KEY")

        if not key:
            raise RuntimeError("GOODREADS_KEY is not set")

        # Query api with key and isbn as param
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
        
        # Convert response to JSON 
        response = res.json()

        # 'clean' JSON before passing it to bookDetails
        response = response['books'][0]

        # Append response as the second element on the list
        bookDetails.append(response)

        """ Users review """
        rows = db.execute("SELECT id, isbn, title, author, year FROM books WHERE isbn=:isbn", {"isbn": isbn})

        # Save id into variable
        book = rows.fetchone()
        book_id = book[0]

        # Fetch book review
        results = db.execute("SELECT users.username, comment, rating FROM users INNER JOIN reviews ON users.id = reviews.user_id WHERE book_id=:book_id", {"book_id": book_id})

        reviews = results.fetchall()

        if reviews:
            print(reviews)

        return render_template("book.html", bookDetails=bookDetails, reviews=reviews)

    # request method = POST
    else: 
        currentUser = session["user_id"]
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        rows = db.execute("SELECT id FROM books WHERE isbn=:isbn", {"isbn": isbn})

        book = rows.fetchone()
        book_id = book[0]

        rows2 = db.execute("SELECT * FROM reviews WHERE user_id=:user_id AND book_id=:book_id", {"user_id": currentUser, "book_id": book_id})

        if rows2.rowcount == 1:
            flash("You already submitted a review for this book", 'warning')
            return redirect("/book/" + isbn)

        # rating = int(rating)

        db.execute("INSERT INTO reviews (user_id, book_id, comment, rating) VALUES (:user_id, :book_id, :comment, :rating)", {"user_id": currentUser, "book_id": book_id, "comment": comment, "rating": rating})

        db.commit()

        flash("Review submitted!", 'info')

        return redirect("/book/" + isbn)    

@app.route("/api/<isbn>")
@login_required
def api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).fetchone()

    if not book:
        return render_template("error.html", message="ERROR 404: Invalid ISBN ")

    reviews = db.execute("SELECT * FROM reviews INNER JOIN books ON reviews.book_id = books.id WHERE isbn=:isbn", {"isbn": isbn}).fetchall()

    count = 0
    rate = 0

    for review in reviews:
        count += 1
        rate += review.rating

    if count>0:
        average_rating = rate/count
    else:
        average_rating = 0

    return jsonify(
        title=book.title,
        author=book.author,
        year=book.year,
        isbn=book.isbn,
        review_count=count,
        average_score=average_rating
    )

if __name__ == "__main__":
    app.run(debug=True)