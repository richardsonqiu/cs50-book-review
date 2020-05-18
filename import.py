import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# DATABASE_URL = 'postgres://xtafrcfepfrhkv:1da5e6972ef6a58f22c55d716ca79ad297a6d7eefd350d633aacf8de4c636fa5@ec2-50-17-21-170.compute-1.amazonaws.com:5432/da6g2ambslb4rn'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine('postgres://xtafrcfepfrhkv:1da5e6972ef6a58f22c55d716ca79ad297a6d7eefd350d633aacf8de4c636fa5@ec2-50-17-21-170.compute-1.amazonaws.com:5432/da6g2ambslb4rn')
db = scoped_session(sessionmaker(bind=engine))

file = open("books.csv")

reader = csv.reader(file)

next(reader)

for isbn, title, author, year in reader:
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", 
    {"isbn": isbn, "title": title, "author": author, "year": year})

    print(f"Added book {title} to database.")

    db.commit()