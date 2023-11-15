"""
This module defines a Flask app that serves a portfolio view.
"""

import datetime
import functools
import json
import logging

from waitress import serve
from flask import Flask, abort, jsonify, request, send_from_directory, session

from util import cache_results, ensure_users_table_exists
import business as business
import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__, static_folder=os.path.join(os.getcwd(), "frontend/build"))
app.secret_key = os.urandom(24)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("util").setLevel(logging.INFO)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.ERROR
)

logging = logging.getLogger(__name__)


def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return (
                jsonify({"error": "You must be logged in to access this resource"}),
                403,
            )
        return func(*args, **kwargs)

    return wrapper


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_file(path):
    return send_from_directory(app.static_folder, path)


@app.route("/portfolio", methods=["GET"])
@app.route("/portfolio/<datestr>", methods=["GET"])
@login_required
def portfolio_json(datestr=None):
    """
    Returns a portfolio view as a JSON object.
    """
    validate_date(datestr)

    json_result = None
    conn_string = get_connection_string()
    if conn_string:
        json_result = business.get_portfolio(
            conn_string=conn_string, request_date=datestr
        )
    if json_result:
        return jsonify(json_result), 200
    return jsonify({"error": "No portfolio data found"}), 400


@app.route("/rebalance/<fromDate>/<todate>", methods=["GET"])
@login_required
def rebalance_json(todate=None, fromDate=None):
    """
    Returns a portfolio view as a JSON object.
    """
    validate_date(todate)
    validate_date(fromDate)

    json_result = None
    conn_string = get_connection_string()
    if conn_string:
        json_result = business.get_rebalance(
            conn_string=conn_string, from_date=todate, to_date=fromDate
        )
    if json_result:
        return jsonify(json_result), 200
    return jsonify({"error": "No portfolio data found"}), 400


@app.route("/nifty200", methods=["GET"])
@app.route("/nifty200/<datestr>", methods=["GET"])
@login_required
def nifty200_json(datestr=None):
    """
    Returns the NIFTY 200 index as a JSON object.
    """
    validate_date(datestr)

    json_result = None
    conn_string = get_connection_string()
    if conn_string:
        json_result = business.get_nifty200(
            conn_string=conn_string, request_date=datestr
        )
    if json_result:
        return jsonify(json_result), 200
    return jsonify({"error": "No NIFTY 200 data found"}), 400


@app.route("/portfolio/<datestr>/<numstocks>/<investment>", methods=["GET"])
@login_required
def portfolio_json_with_params(datestr=None, numstocks=None, investment=None):
    """
    Returns a portfolio view as a JSON object.
    """
    validate_date(datestr)
    ## Validate numstocks and investment
    try:
        numstocks = int(numstocks)
        investment = float(investment)
    except ValueError:
        abort(
            400,
            description="Invalid numstocks or investment. Expected integer and float respectively.",
        )

    json_result = None
    conn_string = get_connection_string()
    if conn_string:
        json_result = business.get_portfolio_with_params(
            conn_string=conn_string,
            request_date=datestr,
            num_stocks=numstocks,
            investment=investment,
        )
    if json_result:
        return jsonify(json_result), 200
    return jsonify({"error": "No portfolio data found"}), 400


@app.route("/rebalance/<todate>/<fromDate>/<numstocks>/<investment>", methods=["GET"])
@login_required
def rebalance_json_with_params(
    todate=None, fromDate=None, numstocks=None, investment=None
):
    """
    Returns a portfolio view as a JSON object.
    """
    validate_date(todate)
    validate_date(fromDate)
    ## Validate numstocks and investment
    try:
        numstocks = int(numstocks)
        investment = float(investment)
    except ValueError:
        abort(
            400,
            description="Invalid numstocks or investment. Expected integer and float respectively.",
        )

    json_result = None
    conn_string = get_connection_string()
    if conn_string:
        json_result = business.get_rebalance_with_params(
            conn_string=conn_string,
            from_date=todate,
            to_date=fromDate,
            num_stocks=numstocks,
            investment=investment,
        )
    if json_result:
        return jsonify(json_result), 200
    return jsonify({"error": "No portfolio data found"}), 400


@app.route("/register", methods=["POST"])
@ensure_users_table_exists
def register():
    username = request.json.get("username")
    password = request.json.get("password")
    logging.info("Registering user %s", username)
    logging.info("Password is %s", password)
    hashed_password = generate_password_hash(password)
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()
    return jsonify({"success": "User created successfully"}), 201


@app.route("/login", methods=["POST"])
@ensure_users_table_exists
def login():
    username = request.json.get("username")
    password = request.json.get("password")
    logging.info("Registering user %s", username)
    logging.info("Password is %s", password)
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result is None:
        return jsonify({"error": "Invalid username or password"}), 400
    hashed_password = result[0]
    if check_password_hash(hashed_password, password):
        session["username"] = username
        return jsonify({"success": "Logged in successfully"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 400


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"success": "Logged out successfully"}), 200

@app.route("/islogged/<username>", methods=["GET"])
def islogged(username):
    if "username" in session and session["username"] == username:
        ## simply return ok
        return jsonify({"success": "Logged in successfully"}), 200
    else:
        return jsonify({"error": "Not logged in"}), 400

@app.route("/test", methods=["GET"])
@login_required
def portfolio():
    """
    Returns a portfolio view as an HTML table.

    Returns:
        str: The HTML table as a string.
    """
    conn_string = get_connection_string()
    if conn_string:
        table_html = business.view_portfolio(
            conn_string=conn_string, detailed_view=False
        )
        # table_html is string, return it as html
        if table_html:
            logging.info("Portfolio found")
            return table_html
    return jsonify({"error": "No portfolio data found"}), 400


@cache_results
def get_connection_string():
    """
    Returns the connection string from local.settings.json.
    """
    conn_string = None
    try:
        # Read local.settings.json
        with open("local.settings.json", encoding="utf-8") as json_file:
            data = json.load(json_file)
            conn_string = data["Values"]["AzureWebJobsStorage"]
    except FileNotFoundError as e:
        logging.error("local.settings.json not found: %s", e)
    except json.JSONDecodeError as e:
        logging.error("Error reading local.settings.json: %s", e)
    return conn_string


def generate_portfolio():
    """
    Generates today's portfolio using the momentum strategy.

    Reads the connection string and strategy parameters from local.settings.json.
    """
    conn_string = None
    num_stocks = None
    investment_amount = None
    try:
        # Read local.settings.json
        with open("local.settings.json", encoding="utf-8") as json_file:
            data = json.load(json_file)
            conn_string = data["Values"]["AzureWebJobsStorage"]
            num_stocks = int(data["Values"]["NUM_STOCKS"])
            investment_amount = float(data["Values"]["INVESTMENT_AMOUNT"])
    except FileNotFoundError as e:
        logging.error("local.settings.json not found: %s", e)
    except json.JSONDecodeError as e:
        logging.error("Error reading local.settings.json: %s", e)
    if conn_string and num_stocks and investment_amount:
        business.build_todays_portfolio(conn_string, num_stocks, investment_amount)
        logging.info("Momentum strategy portfolio successfully built!")
    else:
        logging.error("Error building momentum strategy")


def validate_date(datestr):
    try:
        if datestr:
            datetime.datetime.strptime(datestr, "%Y-%m-%d")  # Validate date format
    except ValueError:
        abort(400, description="Invalid date format. Expected YYYY-MM-DD.")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "generate":
        generate_portfolio()
    else:
        serve(app, host="0.0.0.0", port=8000)
        # app.run(host="0.0.0.0", port=8000)
