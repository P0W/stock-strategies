import csv
import itertools
import json
import math
import sys
from py5paisa import FivePaisaClient
import redis
import pyotp
import datetime
import logging
from multiprocessing import Pool

logging.basicConfig(level=logging.INFO)


class Client:
    ACCESS_TOKEN_KEY = "access_token"

    # implement all the abstract methods here
    def __init__(self, cred_file: str = "creds.json"):
        with open(cred_file, encoding="utf-8") as cred_fh:
            self.cred = json.load(cred_fh)
        self._client = None

    def login(self):
        self._client = FivePaisaClient(self.cred)
        try:
            redis_client = redis.Redis(host="127.0.0.1")
            access_token = redis_client.get(Client.ACCESS_TOKEN_KEY)
            if access_token:
                access_token = access_token.decode("utf-8")
                # 5paisa hack, no way to set acess token directly using sdk API
                self._client.client_code = self.cred["clientcode"]
                self._client.access_token = access_token
                self._client.Jwt_token = access_token
            else:
                raise Exception("No access token found")
        except Exception:
            print("No access token found in cache, logging in")
            totp = pyotp.TOTP(self.cred["totp_secret"])
            access_token = self._client.get_totp_session(
                self.cred["clientcode"], totp.now(), self.cred["pin"]
            )
            try:
                redis_client.set(
                    Client.ACCESS_TOKEN_KEY, access_token, ex=2 * 60 * 60
                )  # 2 hours expiry
            except Exception:
                pass
        return self._client


def scrip_master():
    fileName = "scripmaster-csv-format.csv"
    ## headers Exch,ExchType,Scripcode,Name,Series,Expiry,CpType,StrikeRate,WireCat,ISIN,FullName,LotSize,AllowedToTrade,QtyLimit,Multiplier,Underlyer,Root,TickSize,CO BO Allowed
    ## read file using pandas
    import pandas as pd

    df = pd.read_csv(fileName)
    ## get only ScripCode and Name for all Series = 'EQ' and Exch = 'N' and ExchType = 'C'
    df = df[(df["Series"] == "EQ") & (df["Exch"] == "N") & (df["ExchType"] == "C")]
    df = df[["Scripcode", "Name"]]
    ## convert to disct with Name as key and Scripcode as value
    scrip_dict = df.set_index("Name").T.to_dict("list")
    ## value should be one element
    for key, value in scrip_dict.items():
        scrip_dict[key] = value[0]
    ## return
    return scrip_dict


def get_historical_prices():
    d = scrip_master()
    client_connection = Client()
    client = client_connection.login()
    ## todays date in format yyyy-mm-dd

    ## read stocks-nifty-200-2023-10-05.json
    with open("stocks-nifty-200-2023-10-05.json", "r") as f:
        nifty_200 = json.load(f)

    symbols = set()
    for stock in nifty_200:
        symbols.add(stock["symbol"])

    today = datetime.datetime.now()
    today = today.strftime("%Y-%m-%d")
    six_months_before = datetime.datetime.now() - datetime.timedelta(days=365 * 2)
    results = {}
    count = 0
    for scrip_name, scrip_code in d.items():
        if scrip_name not in symbols:
            logging.info(f"{scrip_name} not in nifty 200")
            continue
        try:
            # logging.info(f"Getting historical data for {scrip_name} {scrip_code}")
            df = client.historical_data(
                "N", "C", scrip_code, "1d", six_months_before, today
            )
            ## get only Date, Close and Volume
            df = df[["Datetime", "Close", "Volume"]]
            ## rename Close to lp and Volume to v
            df = df.rename(columns={"Close": "lp", "Volume": "v"})
            ## convert to list of dict
            df = df.to_dict("records")
            ## add to results
            results[scrip_name] = df
            if count % 10 == 0:
                logging.info(f"Completed {count} stocks")
            count += 1
            # if count > 15:
            #     break

        except Exception as e:
            logging.error(e)
            continue
    ## For given date add all stocks and their close price and volume
    per_day_data = {}
    for stock, data in results.items():
        for item in data:
            date = item["Datetime"].split("T")[0]
            if date not in per_day_data:
                per_day_data[date] = {}
            per_day_data[date][stock] = {
                "lp": item["lp"],
                "volume": item["v"],
                "returns": {},
            }

    ## calculate weekly, monthly and yearly returns

    previous_date = None
    date_list = list(per_day_data.keys())
    logging.info(f"Total days {len(date_list)}")
    for days, days_str in [(1, "1d"), (7, "1w"), (30, "1mo"), (365, "1y")]:
        count_days = 0
        for current_date, stocks in per_day_data.items():
            diff = count_days - days
            try:
                if count_days >= days and diff >= 0:
                    past_day = date_list[diff]
                    previous_date = per_day_data[past_day]
                    for stock, data in stocks.items():
                        ## calculate returns
                        try:
                            data["returns"][days_str] = (
                                data["lp"] - previous_date[stock]["lp"]
                            ) / previous_date[stock]["lp"]
                        except Exception as e:
                            logging.error(e)
                    # logging.info(f"Now setting previous day to {count_days}")
            except Exception as e:
                logging.error(e)
                logging.error(f"count_days {count_days} diff {diff} {days_str}")

            count_days += 1

    ## write to file
    with open("historical-prices.json", "w") as f:
        json.dump(per_day_data, f, indent=2)


def rebalance_portfolio(day1_stock_info, day2_stock_info, current_day_price_dict):
    capital_incurred = 0
    result = {"stocks": [], "capital_incurred": ""}

    # Calculate the current value of each stock on Day 2
    for stock, info in day1_stock_info.items():
        shares_day1 = info.get("shares", 0)
        shares_day2 = day2_stock_info.get(stock, {}).get("shares", 0)
        price_day2 = current_day_price_dict[stock]
        amount = (shares_day2 - shares_day1) * price_day2
        result["stocks"].append(
            {
                "symbol": stock,
                "shares": shares_day2 - shares_day1,
                "amount": amount,
            }
        )
        # Calculate the profit or loss for this stock
        capital_incurred += amount

    # Calculate the new stocks to buy on Day 2
    for stock, info in day2_stock_info.items():
        if not stock in day1_stock_info:
            shares_day2 = info.get("shares", 0)
            price_day2 = current_day_price_dict[stock]
            amount = shares_day2 * price_day2
            result["stocks"].append(
                {"symbol": stock, "shares": shares_day2, "amount": amount}
            )
            capital_incurred += amount  ## Buy new stocks

    ##  sort the list of dictionaries based on the "shares" value in ascending order
    ##  so that the "no change" items come first, followed by "sold" items, and then "bought" items.
    result["stocks"] = sorted(
        result["stocks"],
        key=lambda x: (x["shares"] == 0, x["shares"] < 0, -x["amount"]),
        reverse=True,
    )

    result["capital_incurred"] = capital_incurred
    return capital_incurred


def run(top_n=25, investment_amount=250000, rebalance_days=15, historical_prices=None):
    with open("historical-prices.json", "r") as f:
        historical_prices = json.load(f)
    results = {}
    TOP_N = top_n
    INVESTMENT_AMOUNT = investment_amount
    REBALANCE_DAYS = rebalance_days
    current_day_portfolio = None
    previous_day_portfolio = None
    rebalance_updates = {}
    days_count = None
    prev_date = None
    for date, stocks in historical_prices.items():
        for stock, data in stocks.items():
            if "1y" in data["returns"]:
                if not date in results:
                    results[date] = [
                        {
                            "symbol": stock,
                            "lp": data["lp"],
                            "v": data["volume"],
                            "returns": data["returns"],
                        }
                    ]
                results[date].append(
                    {
                        "symbol": stock,
                        "lp": data["lp"],
                        "v": data["volume"],
                        "returns": data["returns"],
                    }
                )
            ## sort by returns
        if date in results:
            price_dict = {stock["symbol"]: stock["lp"] for stock in results[date]}
            results[date].sort(
                key=lambda x: x["returns"]["1y"]
                + x["returns"]["1w"] * 52
                + x["returns"]["1mo"] * 12
                + x["returns"]["1d"] * 365,
                reverse=True,
            )
            ## take only top TOP_N
            results[date] = results[date][:TOP_N]
            ## if Rs INVESTMENT_AMOUNT is invested equally in all TOP_N stocks then each stock will
            ## get INVESTMENT_AMOUNT/TOP_N amount, get number of shares
            for stock in results[date]:
                stock["shares"] = int(INVESTMENT_AMOUNT / TOP_N / stock["lp"])
                stock["investment"] = stock["shares"] * stock["lp"]
            current_day_portfolio = {
                stock["symbol"]: {
                    "shares": stock["shares"],
                    "investment": stock["investment"],
                    "price": stock["lp"],
                }
                for stock in results[date]
            }
            days_count = 1 if not days_count else days_count + 1
            if (
                previous_day_portfolio
                and current_day_portfolio
                and days_count
                and days_count % (REBALANCE_DAYS + 1) == 0
            ):
                rebalance_updates[date] = rebalance_portfolio(
                    previous_day_portfolio, current_day_portfolio, price_dict
                )
                # logging.info(f"Rebalancing on {date} with {prev_date} Captital Incurred: {rebalance_updates[date]}")
                previous_day_portfolio = current_day_portfolio
                prev_date = date
            if not previous_day_portfolio:
                prev_date = date
                previous_day_portfolio = current_day_portfolio
    ## write to file
    # with open("historical-prices-sorted.json", "w") as f:
    #     json.dump(results, f, indent=2)
    # with open("rebalance-updates.json", "w") as f:
    #     json.dump(rebalance_updates, f, indent=2)
    ## sum keys of rebalance_updates
    total_capital_incurred = sum(rebalance_updates.values())
    ## logging.info(f"Total capital incurred {total_capital_incurred}")
    ## calculate cagr
    ## get first and last date
    first_date = list(rebalance_updates.keys())[0]
    last_date = list(rebalance_updates.keys())[-1]
    ## calculate cagr
    days = (
        datetime.datetime.strptime(last_date, "%Y-%m-%d")
        - datetime.datetime.strptime(first_date, "%Y-%m-%d")
    ).days + rebalance_days
    cagr = math.pow((investment_amount - total_capital_incurred) / investment_amount,  365.0 / days) - 1

    return total_capital_incurred, round(cagr * 100.0, 2), days


def run_with_parameters(parameters):
    top_n, rebalance_days, investment_amount = parameters
    total_capital_incurred, cagr, days = run(
        top_n=top_n,
        rebalance_days=rebalance_days,
        investment_amount=investment_amount,
    )
    return top_n, rebalance_days, investment_amount, total_capital_incurred, cagr, days


if __name__ == "__main__":
    get_historical_prices()

    ## permute top_n, investment_amount, rebalance_days
    # top_n = [10, 15, 20, 25]
    # rebalance_days = [1, 7, 15, 30]
    # investment_amount = [250000, 500000]
    # Define the parameter values and their corresponding names

    # Define the parameter values
    parameter_values = {
        "top_n": [5, 10, 12, 15, 20, 25, 30],
        "rebalance_days": [1, 7, 15, 30, 90, 120],
        "investment_amount": [250000, 500000],
    }

    # Generate all possible combinations of the parameters
    parameter_combinations = itertools.product(
        parameter_values["top_n"],
        parameter_values["rebalance_days"],
        parameter_values["investment_amount"],
    )

    # Create a Pool with the number of processes you want to use
    with Pool(processes=8) as pool:
        # Use the Pool.map function to execute run_with_parameters in parallel
        results = pool.map(run_with_parameters, parameter_combinations)

    sorted_results = sorted(results, key=lambda x: x[4], reverse=True)

    # Define the CSV file name
    csv_file = "output.csv"

    # Write the results to a CSV file
    with open(csv_file, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write the header row
        csv_writer.writerow(
            [
                "top_n",
                "rebalance_days",
                "investment_amount",
                "total_capital_incurred",
                "cagr",
                "days",
            ]
        )
        # Write the results rows
        csv_writer.writerows([r for r in sorted_results])

    print(f"Results have been written to {csv_file}")
