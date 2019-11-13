import os
import time

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import current_stocks, apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance.db")
db = sqlite3.connect('finance.db')

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    row_users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session.get("user_id"))
    username = row_users[0]["username"]
    cash = row_users[0]["cash"]
    new_table = username + "_index"
    matrix_index = db.execute("SELECT * FROM :new_table", new_table=new_table)
    total = cash
    count = 0
    for count in range(len(matrix_index)):
        total +=matrix_index[count]["total"]

    return render_template("index.html", matrix_index=matrix_index, cash=cash, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        if lookup(request.form.get("symbol")):

            #if request.form.get("shares").isdigit():
            try:
                shares = int(request.form.get("shares"))
                if shares < 0:
                    return apology("Shares must be positive integer")
            except:
                return apology("Shares must be positive integer")

            dictionary = lookup(request.form.get("symbol"))
            price = float(dictionary["price"])
            price = round(price, 2)
            total_price = price * shares

            rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session.get("user_id"))
            username = rows[0]["username"]

            cash = float(rows[0]["cash"])
            cash = round(cash, 2)

            if ((cash - total_price) < 0):
                return apology("Insufficient funds", 400)

            else:

                new_table = username + "_index"
                matrix_index = db.execute("SELECT * FROM :new_table WHERE symbol=:symbol" \
                , new_table=new_table, symbol=dictionary["symbol"])

                if (len(matrix_index) != 0):
                    row = db.execute("SELECT * FROM :new_table WHERE symbol = :symbol", \
                    new_table=new_table, symbol=dictionary["symbol"])

                    db.execute("UPDATE :new_table SET 'shares'= :shares \
                    , 'price'= :price, 'total'= :total WHERE symbol = :symbol", \
                    new_table=new_table, shares=row[0]["shares"]+int(request.form.get("shares")), \
                    price=float(dictionary["price"]), total=(row[0]["shares"]+int(request.form.get("shares"))) * \
                    float(dictionary["price"]), symbol=dictionary["symbol"])

                else:
                    row = db.execute("SELECT * FROM :new_table WHERE symbol = :symbol", \
                    new_table=new_table, symbol=dictionary["symbol"])

                    db.execute("INSERT INTO :new_table(symbol, name, shares, price, total) \
                    VALUES (:symbol, :name, :shares, :price, :total)", new_table=new_table \
                    , symbol=dictionary["symbol"], name=dictionary["name"], shares=int(request.form.get("shares")) \
                    , price=float(dictionary["price"]), total=(int(request.form.get("shares"))) * \
                    float(dictionary["price"]))

                #insert the id, symble, name, shares, price, total, time in the table

                db.execute("INSERT INTO :username(symbol, name, shares, price, time) \
                VALUES (:symbol, :name, :shares, :price, :time)" \
                , username=username, symbol=dictionary["symbol"], name=dictionary["name"], shares=shares, price=price, \
                time=time.strftime('%Y-%m-%d %H:%M:%S'))

                db.execute("UPDATE 'users' SET 'cash'= :cash WHERE id = :user_id", cash=(cash - total_price), user_id=session.get("user_id"))

                return redirect("/")

        else:
            return apology("The stock does not exist", 400)

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    rows_users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session.get("user_id"))

    username = rows_users[0]["username"]
    matrix_history = db.execute("SELECT * FROM :username", username = username)

    return render_template("history.html", matrix = matrix_history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":

        if lookup(request.form.get("symbol")):

            dictionary = lookup(request.form.get("symbol"))
            dictionary["price"] = usd(dictionary["price"])
            return render_template("quote_result.html", name=dictionary["name"], price=dictionary["price"], symbol=dictionary["symbol"])

        else:
            return apology("INVALID SYMBOL", 400)

    elif request.method == "GET":
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""


    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username_n = request.form.get("username")
        password_n = request.form.get("password")
        password_a = request.form.get("confirmation")
        password_h = generate_password_hash(request.form.get("password"))

        # Ensure username was submitted
        if not username_n:
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not password_n:
            return apology("must provide password", 400)

        if password_n != password_a:
            return apology("must type the same password", 400)

        if not username_n.isalnum():
            return apology("Invalid username", 400)

        if username_n.find('\'') != -1 or username_n.find(';') != -1:
            return apology("Invalid username", 400)


        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username_n)

        if len(rows) == 1:
            return apology("the username was exist", 400)

        else:

            db.execute("INSERT INTO 'users' (username, hash) VALUES (:username, :hash_p)",username = username_n,  hash_p = password_h)

            rows = db.execute("SELECT * FROM users WHERE username = :username", username=username_n)

            # Remember which user has logged in

            db.execute("CREATE TABLE :username ( \
                        'order' INTEGER PRIMARY KEY, \
                        'symbol' TEXT, 'name' TEXT, \
                        'shares' INTEGER, \
                        'price' NUMERIC, \
                        'time' DATETIME)", username = username_n)

            new_table = username_n + "_index"

            db.execute("CREATE TABLE :new_table ( \
                        'order' INTEGER PRIMARY KEY, \
                        'symbol' TEXT, \
                        'name' TEXT, \
                        'shares' INTEGER, \
                        'price' NUMERIC, \
                        'total' NUMERIC)", new_table = new_table)


            session["user_id"] = rows[0]["id"]

            # Redirect user to home page
            return redirect("/", 200)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    #matrix_index = [['symbol', 'name', shares, 'price', 'total'] * the number of stocks you have]
    #---------------------------------get the matrix of index page-------------------------------------------
    rows_users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session.get("user_id"))
    username = rows_users[0]["username"]

    new_table = username + "_index"
    matrix_index = db.execute("SELECT * FROM :new_table", new_table = new_table)
    len_column = len(matrix_index)

    if request.method == "POST":

        rows_users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session.get("user_id"))
        username = rows_users[0]["username"]

        # get the string of "symbol & shares"
        if request.form.get("symbol") == None:
            return apology("Please select a stock", 400)

        if lookup(request.form.get("symbol")):

            new_table = username + "_index"
            row_index = db.execute("SELECT * FROM :new_table WHERE symbol= :symbol",
            new_table = new_table, symbol=request.form.get("symbol"))
            current_shares = row_index[0]["shares"]

            # how many shares you want to sell

            try:
                sell_shares = int(request.form.get("shares"))

                if sell_shares < 0 or current_shares < sell_shares:
                    return apology("You don't have enough shares", 400)

            except:
                return apology("error", 400)

            dictionary = lookup(request.form.get("symbol"))
            price = float(dictionary["price"])
            price = round(price, 2)
            total_price = sell_shares * price

            rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session.get("user_id"))

            cash = float(rows[0]["cash"])
            cash = round(cash, 2)

            '''row_index = db.execute("SELECT * FROM :new_table WHERE symbol = :symbol", \
            new_table=new_table, symbol=dictionary["symbol"])'''

            db.execute("UPDATE :new_table SET 'shares'= :shares \
            , 'price'= :price, 'total'= :total WHERE symbol = :symbol", \
            new_table=new_table, shares=row_index[0]["shares"]-int(request.form.get("shares")), \
            price=float(dictionary["price"]), total=(row_index[0]["shares"]-int(request.form.get("shares"))) * \
            float(dictionary["price"]), symbol=dictionary["symbol"])


            #insert the id, symble, name, shares, price, total, buy_time(empty), sell_time in the table
            db.execute("INSERT INTO :username(symbol, name, shares, price, time) \
            VALUES (:symbol, :name, :shares, :price, :time)" \
            , username=username, symbol=dictionary["symbol"], name=dictionary["name"], shares=-sell_shares, price=price, \
            time=time.strftime('%Y-%m-%d %H:%M:%S'))

            db.execute("UPDATE 'users' SET 'cash'= :cash WHERE id = :user_id", cash=cash + total_price, user_id=session.get("user_id"))
            flash("Sold!")
            return redirect("/")

        else:
            return apology("Invalid symbol", 400)
    else:
        return render_template("sell.html", matrix = matrix_index, len_column = len_column)

@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    if request.method == "POST":
        rows_users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session.get("user_id"))

        password_o = request.form.get("password_o")
        password_n = request.form.get("password_n")
        password_a = request.form.get("confirmation")

        if not check_password_hash(rows_users[0]["hash"], password_o):
            return apology("Old password is wrong", 400)
        else:
            if password_n != password_a:
                return apology("must type the same password", 400)
            else:
                password_n = generate_password_hash(password_n)
                db.execute("UPDATE 'users' SET 'hash'= :password WHERE id = :user_id", password=password_n, \
                user_id=session.get("user_id"))

        flash("Change password sucessfully! Please log in again!")
        session.clear()
        return redirect("/login")

    else:
        return render_template("change.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
