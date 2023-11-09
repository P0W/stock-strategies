"""
This module defines a Flask app that serves a portfolio view.
"""

import datetime
import json
import logging

from waitress import serve
from flask import Flask, jsonify, send_from_directory

from util import cache_results
import business

app = Flask(__name__, static_folder="build")
logger = logging.getLogger(__name__)


@app.route("/show")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_file(path):
    return send_from_directory(app.static_folder, path)


@app.route("/json", methods=["GET"])
@app.route("/json/<datestr>", methods=["GET"])
def portfolio_json(datestr=None):
    """
    Returns a portfolio view as a JSON object.
    """
    if datestr:
        try:
            datetime.strptime(datestr, "%Y-%m-%d")  # Validate date format
        except ValueError:
            return (
                jsonify({"error": "Incorrect date format, should be YYYY-MM-DD"}),
                400,
            )

    json_result = None
    conn_string = get_connection_string()
    if conn_string:
        json_result = business.get_portfolio(
            conn_string=conn_string, request_date=datestr
        )
    if json_result:
        return jsonify(json_result), 200
    return jsonify({"error": "No portfolio data found"}), 400


@app.route("/", methods=["GET"])
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
            logger.info("Portfolio found")
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
        logger.error("local.settings.json not found: %s", e)
    except json.JSONDecodeError as e:
        logger.error("Error reading local.settings.json: %s", e)
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
        logger.error("local.settings.json not found: %s", e)
    except json.JSONDecodeError as e:
        logger.error("Error reading local.settings.json: %s", e)
    if conn_string and num_stocks and investment_amount:
        business.build_todays_portfolio(conn_string, num_stocks, investment_amount)
        logger.info("Momentum strategy portfolio successfully built!")
    else:
        logger.error("Error building momentum strategy")


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000)
