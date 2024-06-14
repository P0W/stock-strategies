"""Create backtest portfolio and trade on 5paisa"""

import json
import os
import sys
import string
from math import ceil
import logging
import datetime as dt
import argparse

import pandas as pd
import pyotp
import requests
from py5paisa import FivePaisaClient
from py5paisa.order import Basket_order


logging.basicConfig(
    level=logging.DEBUG,
    ## pylint: disable=line-too-long
    format="%(asctime)s [%(levelname)s] %(name)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Set logging level for `requests` to WARNING to suppress DEBUG logs
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


def get_portfolio(investment_amount, num_stocks, back_days=4):
    """Get portfolio with params"""
    base_url = r"https://stocks.eastus.cloudapp.azure.com/"
    data = {
        "username": "trialuser",
        "hashedPassword": "1de04c49ce1b1bd6c8ce2af8f69213c3013cf2dbf4309cad043a4074c97a5156",
    }
    try:
        data = json.dumps(data)
        headers = {"Content-Type": "application/json"}

        with requests.Session() as session:
            session.headers = headers
            session.verify = False

            response = session.post(base_url + "login", data=data)

            if response.status_code == 200:
                logging.info("Login Successful")
                today_date = dt.datetime.now().date()
                previous_date = today_date - dt.timedelta(days=back_days)
                previous_date = previous_date.strftime("%Y-%m-%d")
                logging.debug("Today date : %s", today_date)
                logging.debug("Previous date : %s", previous_date)
                response = session.get(
                    base_url
                    + f"rebalance/{previous_date}/{today_date}/{num_stocks}/{investment_amount}"
                )
                if response.status_code == 200:
                    logging.info("Portfolio info fetched successfully")
                    return response.json()
                logging.error("Error in creating portfolio: %s", response.text)
                return None
            logging.error("Error in login %s", response.text)
            return None
    except Exception as e:  ## pylint: disable=broad-except
        logging.error("Error in getting portfolio: %s", e)
        return None


def client_login(creds_file="creds.json"):
    """Login to 5paisa"""
    try:
        with open(creds_file, "r", encoding="utf-8") as f:
            cred = json.load(f)
            client = FivePaisaClient(cred)
            totp = pyotp.TOTP(cred["totp_secret"])
            client.get_totp_session(cred["clientcode"], totp.now(), cred["pin"])
            return client
    except Exception as e:  ## pylint: disable=broad-except
        logging.error("Error in login to 5paisa: %s", e)
    return None


def create_basket_order(client, portfolio_data_frame, basket_letter="A"):
    """Create basket order"""
    today_date = dt.datetime.now().date().strftime("%Y%m%d")
    basket_name = f"Momentum{basket_letter}{today_date}"
    try:
        response = client.create_basket(basket_name)
        basket_list = [{"BasketID": str(response["BasketId"])}]
        for _, row in portfolio_data_frame.iterrows():
            scrip_code = row["Scripcode"]
            scrip_code = str(scrip_code)
            full_name = row["Name"]
            shares = int(row["shares"])
            exchange = row["Exch"]
            # price = round(float(row["price"]) * 10, 2)
            if shares == 0:
                continue
            if shares < 0:
                order_type = "SELL"
                shares = abs(shares)
            else:
                order_type = "BUY"
            order_to_basket = Basket_order(
                ScripCode=scrip_code,
                Qty=shares,
                Price=0,  ## Market order
                OrderType=order_type,
                Exchange=exchange,
                ExchangeType="C",
                AtMarket=True,
                DelvIntra="D",
            )
            # order_to_basket = Basket_order("N","C",23000,"BUY",shares,"1660","I")
            client.add_basket_order(order_to_basket, basket_list)
            logging.info(
                "%3s %5d shares of %15s using basket %25s",
                order_type,
                shares,
                full_name,
                basket_name,
            )
    except Exception as e:  ## pylint: disable=broad-except
        logging.error("Error in creating basket order: %s", e)


def download_scrip_master():
    """Download portfolio"""
    today_date = dt.datetime.now().date().strftime("%Y-%m-%d")
    file_name = f"scrip_master_{today_date}.csv"
    if os.path.exists(file_name):
        logging.info("Scrip master already downloaded")
    else:
        try:
            base_url = r"https://images.5paisa.com/website/scripmaster-csv-format.csv"
            res = requests.get(base_url, timeout=10)
            if res.status_code == 200:
                logging.info("Scrip master downloaded successfully")

                with open(file_name, "wb") as f:
                    f.write(res.content)
        except Exception as e:  ## pylint: disable=broad-except
            logging.error("Error in downloading scrip master: %s", e)
            return None
    ## read csv
    df = pd.read_csv(file_name)
    # Exch,ExchType,Scripcode,Name,FullName
    df = df[["Exch", "ExchType", "Scripcode", "Name", "Series", "FullName"]]
    df = df[df["ExchType"] == "C"]
    df = df[df["Series"] == "EQ"]
    # df = df.sort_values(by='Exch', ascending=False).drop_duplicates(subset=['Scripcode'], keep='first')
    df = df[["Scripcode", "Name", "Exch", "FullName"]]
    ## if two scrip codes are same, keep the one which Exch is B
    df = df.sort_values(by="Exch", ascending=True).drop_duplicates(
        subset=["Name"], keep="first"
    )
    return df


def remove_all_baskets(client):
    """Remove all baskets"""
    try:
        response = client.get_basket()
        ## remove all baskets having Momentum in their name
        for data_item in response["Data"]:
            if "Momentum" in data_item["BasketName"]:
                logging.info("Deleting basket %s ...", data_item["BasketName"])
                response = client.delete_basket([{"BasketID": data_item["BasketId"]}])
                logging.debug(response)
    except Exception as e:  ## pylint: disable=broad-except
        logging.error("Error in deleting baskets: %s", e)


def create_baskets_and_orders(client, portfolio_data_frame):
    """Create baskets and orders for the given portfolio DataFrame"""

    ## Remove stocks with 0 shares
    portfolio_data_frame = portfolio_data_frame[portfolio_data_frame["shares"] != 0]
    # Determine the number of baskets needed
    num_stocks = len(portfolio_data_frame)
    logging.info("Total stocks: %d", num_stocks)
    baskets_needed = ceil(num_stocks / 10)

    ## remove all baskets
    remove_all_baskets(client)

    # Split the DataFrame into chunks of 10
    for i in range(baskets_needed):
        start_idx = i * 10
        end_idx = start_idx + 10
        basket_df = portfolio_data_frame.iloc[start_idx:end_idx]
        logging.debug("Adding total %d stocks to basket %d", len(basket_df), i)

        # Create a basket order for the current chunk
        basket_label = string.ascii_uppercase[i]  # Label baskets as A, B, C, etc.
        logging.info("Creating basket :%s ...", basket_label)
        create_basket_order(client, basket_df, basket_label)


def main(amount, num_of_stocks, back_days):
    """Main function to create portfolio and trade on 5paisa"""
    scrip_df = download_scrip_master()
    client_instance = client_login()
    holdings = client_instance.holdings()
    positions = client_instance.positions()
    positions = {
        item["ScripName"]: {
            "Exch": item["Exch"],
            "shares": item["NetQty"],
            "code": item["ScripCode"]
        }
        if item["ExchType"] == "C"
        else None
        for item in positions
    }
    logging.debug("Positions: %s", json.dumps(positions, indent=2))
    holdings = {
        item["BseCode"]: {
            "Exch": item["Exch"],
            "shares": item["Quantity"],
            "symbol": item["Symbol"],
        }
        for item in holdings
    }
    logging.debug("Holdings: %s", json.dumps(holdings, indent=2))
    portfolio = get_portfolio(amount, num_of_stocks, back_days)
    try:
        portfolio = portfolio["stocks"]
        ## get scrip code from portfolio
        portfolio_df = pd.DataFrame(portfolio)
        portfolio_df = portfolio_df.merge(scrip_df, left_on="symbol", right_on="Name")
        logging.debug("Total stocks in portfolio: %d", len(portfolio_df))
        portfolio_df = portfolio_df[["symbol", "shares", "Scripcode", "Name", "Exch"]]
        logging.debug("Portfolio DataFrame: %s", json.dumps(portfolio, indent=2))
        ## verify if the stocks which are being sold shares <0 are present in holdings
        present_in_holdings = True
        for _, row in portfolio_df.iterrows():
            scrip_code = row["Scripcode"]
            scrip_code = str(scrip_code)
            if row["shares"] < 0:
                if scrip_code not in holdings:
                    if row["symbol"] not in positions:
                        logging.error(
                            "Stock %s|%s|%s is neither in holdings nor in positions. Cannot sell.",
                            row["symbol"],
                            row["Scripcode"],
                            row["Exch"],
                        )
                        present_in_holdings = False
                    else:
                        ## remove the stock from portfolio_df
                        portfolio_df = portfolio_df[portfolio_df["Name"] != row["symbol"]]
                        logging.info(
                            "Stock %s|%s|%s is in positions. Not selling.",
                            row["symbol"],
                            row["Scripcode"],
                            row["Exch"],
                        )
        if not present_in_holdings:
            logging.error("Some stocks are not present in holdings. Exiting.")
            sys.exit(1)
        ## if non empty portfolio
        if not portfolio_df.empty:
            logging.info("Creating backets with %d stocks", len(portfolio_df))
            create_baskets_and_orders(client_instance, portfolio_df)
        else:
            logging.info("No stocks to trade. Baskets not created.")
    except Exception as e:  ## pylint: disable=broad-except
        logging.error("Error in main function: %s", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trade 5paisa stocks.")
    parser.add_argument("--amount", type=int, default=500000, help="Investment amount")
    parser.add_argument(
        "--num_of_stocks", type=int, default=15, help="Number of stocks"
    )
    parser.add_argument(
        "--creds_file",
        type=str,
        default="creds.json",
        help="Credentials file for 5paisa",
    )
    parser.add_argument(
        "--back_days",
        type=int,
        default=4,
        help="Number of days to go back to get portfolio",
    )

    args = parser.parse_args()

    main(args.amount, args.num_of_stocks, args.back_days)
