import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

#db = SQL("sqlite:///finance.db")

def current_stocks(username):

    #rows_users = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=user_id)

    #new_table = 'HISTORY_' + str(user_id)
    matrix_history = db.execute("SELECT * FROM :username", username = username)
    #matrix_history = db.execute("SELECT * FROM {}".format(new_table))
    total = 0

    matrix_index = []
    for i in range(len(matrix_history)):

        if matrix_history[i]["symbol"] != "checked":

            dictionary = lookup(matrix_history[i]["symbol"])
            #int
            current_shares = int(matrix_history[i]["shares"])
            #float
            current_price = float(dictionary["price"])

            for j in range(i + 1, len(matrix_history)):
                if matrix_history[i]["symbol"] == matrix_history[j]["symbol"]:

                    current_shares += int(matrix_history[j]["shares"])
                    matrix_history[j]["symbol"] = "checked"

                #else do nothing

            current_total = current_shares * current_price
            total += current_total

            if i == 0 and current_shares != 0:
                matrix_index = [[matrix_history[i]["symbol"], matrix_history[i]["name"], current_shares,
                usd(current_price), usd(current_total)]]

            elif current_shares == 0:
                continue

            else:
                matrix_index += [[matrix_history[i]["symbol"], matrix_history[i]["name"], current_shares,
                usd(current_price), usd(current_total)]]

        else:
            continue

    #end of for loop

    rows_users = db.execute("SELECT * FROM users WHERE username = :username",
            username=username)

    cash = float(rows_users[0]["cash"])
    total += cash

    cash = usd(cash)
    total = usd(total)

    return matrix_index, cash, total

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    if symbol == "AAAA":
        return {"name": "Test A", "price": 28.00, "symbol": "AAAA"}
    # Contact API
    try:
        response = requests.get(f"https://api.iextrading.com/1.0/stock/{urllib.parse.quote_plus(symbol)}/quote")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
