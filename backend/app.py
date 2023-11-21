"""
This module defines a Flask app that serves a portfolio view.
"""

import datetime
import functools
import hashlib
import json
import logging

from waitress import serve
from flask import Flask, abort, jsonify, request, send_from_directory, session
from flask_session import Session

from util import cache_results, redis_client
import business as business
import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__, static_folder=os.path.join(os.getcwd(), "frontend/build"))
app.secret_key = os.urandom(24)
# Configure Flask-Session
# Use Redis session interface
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = redis_client

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("util").setLevel(logging.INFO)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.ERROR
)

logging = logging.getLogger(__name__)

# Initialize the Flask-Session extension
Session(app)


def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if "username" not in session and not app.debug:
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
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_from_directory(app.static_folder, "index.html")


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
        porfolio_data, tickertape_links = business.get_portfolio_with_params(
            conn_string=conn_string,
            request_date=datestr,
            num_stocks=numstocks,
            investment=investment,
        )
        json_result = {
            "portfolio": porfolio_data,
            "tickertape_links": tickertape_links,
        }
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
def register():
    username = request.json.get("username")
    hashed_password = request.json.get("hashedPassword")
    password = hashlib.sha256(hashed_password.encode()).hexdigest()
    hashed_password = generate_password_hash(password)

    # Get email, phoneNumber, name
    email = request.json.get("email")
    phoneNumber = request.json.get("phoneNumber")
    fullName = request.json.get("fullName")

    # Check if username already exists
    if redis_client.hexists("users", username):
        return jsonify({"error": "Username already exists"}), 400

    # Get the next ID
    user_id = redis_client.incr("user_id")

    # Store the user data in Redis
    redis_client.hset("users", username, hashed_password)
    redis_client.hset("user_ids", username, user_id)

    ## Store the user data: email, phoneNumber, name in Redis
    redis_client.hset(
        "users_profile",
        username,
        json.dumps(
            {
                "email": email,
                "phoneNumber": phoneNumber,
                "fullName": fullName,
                "num_stocks": 15,
                "investment": 5000000,
            }
        ),
    )

    return jsonify({"success": "User created successfully", "id": user_id}), 201


@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username")
    hashed_password = request.json.get("hashedPassword")
    password = hashlib.sha256(hashed_password.encode()).hexdigest()
    # Get the hashed password from Redis
    hashed_password = redis_client.hget("users", username)
    if hashed_password is not None:
        hashed_password = hashed_password.decode("utf-8")

    # Check if the username exists and the password is correct
    if hashed_password is None or not check_password_hash(hashed_password, password):
        return jsonify({"error": "Invalid username or password"}), 400

    # Get the user ID from Redis
    user_id = redis_client.hget("user_ids", username)
    # Decode the user ID to a string
    if user_id is not None:
        user_id = user_id.decode("utf-8")
    session["username"] = username

    ## Get the user profile from Redis
    user_profile = redis_client.hget("users_profile", username)
    if user_profile is not None:
        user_profile = json.loads(user_profile.decode("utf-8"))
    else:
        user_profile = {}
    ## jsonify the user profile along with the success message
    user_profile["success"] = "Logged in successfully"
    return (
        jsonify(user_profile),
        200,
    )


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    username = session["username"]
    user_profile = redis_client.hget("users_profile", username)
    if user_profile is not None:
        user_profile = json.loads(user_profile.decode("utf-8"))
    return jsonify(user_profile), 200


@app.route("/profile", methods=["POST"])
@login_required
def update_profile():
    username = session["username"]
    user_profile = redis_client.hget("users_profile", username)
    if user_profile is not None:
        user_profile = json.loads(user_profile.decode("utf-8"))
    else:
        user_profile = {}
    user_profile.update(request.json)
    redis_client.hset("users_profile", username, json.dumps(user_profile))
    return jsonify({"success": "Profile updated successfully"}), 200


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"success": "Logged out successfully"}), 200


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
    elif len(sys.argv) == 2 and sys.argv[1] == "debug":
        ## Debug
        app.run(debug=True, host="0.0.0.0", port=8000)
    else:
        ## Production
        serve(app, host="0.0.0.0", port=8000)
