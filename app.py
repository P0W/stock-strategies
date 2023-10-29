"""
This module defines a Flask app that serves a portfolio view.
"""

import json
import logging

from flask import Flask

import business

app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.route("/", methods=["GET"])
def portfolio():
    """
    Returns a portfolio view as an HTML table.

    Returns:
        str: The HTML table as a string.
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
    if conn_string:
        table_html = business.view_portfolio(conn_string=conn_string, detailed_view=False)
        # table_html is string, return it as html
        if table_html:
            logger.info("Portfolio found")
            return table_html
    return "Portfolio not found"


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
    app.run(host="localhost", port=8000, debug=True)
