import pyotp
import requests
from py5paisa import FivePaisaClient
from py5paisa.order import Basket_order
import datetime as dt
import json
import os
import pandas as pd


def get_portfolio(investment_amount, num_stocks):
    """Get portfolio with params"""
    base_url = r"https://172.174.157.91/"
    data = {
        "username": "trialuser",
        "hashedPassword": "79891e980747ffbd21e690297394efe764fa56d7e37750f800879fbb2d34571a",
    }
    data = json.dumps(data)
    headers = {"Content-Type": "application/json"}

    with requests.Session() as session:
        session.headers = headers
        session.verify = False

        response = session.post(base_url + "login", data=data)

        if response.status_code == 200:
            print("Login Successful")
            today_date = dt.datetime.now().date()
            previous_date = today_date - dt.timedelta(days=1)
            previous_date = previous_date.strftime("%Y-%m-%d")
            response = session.get(
                base_url
                + f"/portfolio/{previous_date}/{num_stocks}/{investment_amount}"
            )

            if response.status_code == 200:
                print("Portfolio info fetched successfully")
                return response.json()
            else:
                print("Error in creating portfolio", response.text)
        else:
            print("Error in login", response.text)


def client_login():
    """Login to 5paisa"""
    with open("creds.json", "r") as f:
        cred = json.load(f)
        client = FivePaisaClient(cred)
        totp = pyotp.TOTP(cred["totp_secret"])
        client.get_totp_session(cred["clientcode"], totp.now(), cred["pin"])
        return client
    return None


def create_basket_order(client, portfolio_df):
    """Create basket order"""
    today_date = dt.datetime.now().date().strftime("%Y%m%d")
    basket_name = f"Momentum{today_date}"
    response = client.get_basket()
    basket_id = None
    for item in response["Data"]:
        if item["BasketName"] == basket_name:
            basket_id = item["BasketId"]
            break
    response = client.delete_basket([{"BasketID": basket_id}])
    response = client.create_basket(basket_name)
    basket_list = [{"BasketID": str(response["BasketId"])}]
    print(basket_list)
    for index, row in portfolio_df.iterrows():
        scrip_code = row["Scripcode"]
        scrip_code = str(scrip_code)
        shares = int(row["shares"])
        price = round(float(row["price"]) * 10, 2)
        order_to_basket = Basket_order(
            ScripCode=scrip_code,
            Qty=shares,
            Price=0,
            OrderType="BUY",
            Exchange="N",
            ExchangeType="C",
            AtMarket=True,
            DelvIntra="D",
        )
        # order_to_basket = Basket_order("N","C",23000,"BUY",shares,"1660","I")
        client.add_basket_order(order_to_basket, basket_list)
    return None


def download_scrip_master():
    """Download portfolio"""
    today_date = dt.datetime.now().date().strftime("%Y-%m-%d")
    file_name = f"scrip_master_{today_date}.csv"
    if os.path.exists(file_name):
        print("Scrip master already downloaded")
    else:
        base_url = r"https://images.5paisa.com/website/scripmaster-csv-format.csv"
        res = requests.get(base_url)
        if res.status_code == 200:
            print("Scrip master downloaded successfully")

            with open(file_name, "wb") as f:
                f.write(res.content)
    ## read csv
    df = pd.read_csv(file_name)
    # Exch,ExchType,Scripcode,Name,FullName
    df = df[["Exch", "ExchType", "Scripcode", "Name", "Series", "FullName"]]
    df = df[df["ExchType"] == "C"]
    df = df[df["Exch"] == "N"]
    df = df[df["Series"] == "EQ"]
    df = df[["Scripcode", "Name", "FullName"]]
    return df


if __name__ == "__main__":
    investment_amount = 500000
    num_stocks = 10
    scrip_df = download_scrip_master()
    client = client_login()
    portfolio = get_portfolio(investment_amount, num_stocks)
    portfolio = portfolio["portfolio"]
    for item in portfolio:
        print(item["symbol"], item["stock"], item["shares"], item["price"])
    ## get scrip code from portfolio
    portfolio_df = pd.DataFrame(portfolio)
    portfolio_df = portfolio_df.merge(scrip_df, left_on="symbol", right_on="Name")
    portfolio_df = portfolio_df[["symbol", "stock", "shares", "price", "Scripcode"]]
    print(portfolio_df)
    create_basket_order(client, portfolio_df)
