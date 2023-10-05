## Author: Prashant Srivastava

import json
import logging
import math
import pathlib
import datetime
import concurrent.futures

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)


class TickerRequest:
    def __init__(self):
        self.cookies = {}
        self.headers = {}
        try:
            with open("cred.json", "r") as fh:
                creds = json.load(fh)
                self.cookies = creds["cookies"]
                self.header = creds["headers"]
        except:
            logging.info("credentials not found using public login")

    def get(self, page):
        return requests.get(page, cookies=self.cookies, headers=self.headers)


## @brief Method to calculate RSI
## @param data_points: list of data points
## @param period: period to calculate RSI
## @return rsi: calculated RSI
def calculate_rsi(data_points, period=14):
    if len(data_points) < period + 1:
        raise ValueError("Insufficient data points to calculate RSI.")

    avg_gain = 0
    avg_loss = 0

    # Calculate average gain and average loss for the first 'period' data points
    for i in range(1, period + 1):
        diff = data_points[i]["lp"] - data_points[i - 1]["lp"]
        if diff > 0:
            avg_gain += diff
        else:
            avg_loss += abs(diff)

    avg_gain /= period
    avg_loss /= period

    # Calculate RS and RSI for the latest data point
    for i in range(period + 1, len(data_points)):
        diff = data_points[i]["lp"] - data_points[i - 1]["lp"]
        if diff > 0:
            avg_gain = ((period - 1) * avg_gain + diff) / period
            avg_loss = ((period - 1) * avg_loss) / period
        else:
            avg_gain = ((period - 1) * avg_gain) / period
            avg_loss = ((period - 1) * avg_loss + abs(diff)) / period

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


## @brief Method to calculate VWAP
## @param data_points: list of data points
## @return vwap: calculated VWAP
def calculate_vwap(data_points):
    total_price_volume = sum(
        data_point["lp"] * data_point["v"] for data_point in data_points
    )
    total_volume = sum(data_point["v"] for data_point in data_points)

    if total_volume == 0:
        raise ValueError("Total volume is zero, cannot calculate VWAP.")

    vwap = total_price_volume / total_volume
    return vwap


# @brief Method to calculate z score
# @param data: list of data points
# @return normalized data
def z_score_normalize(data):
    mean = sum(data) / len(data)
    std_dev = (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5
    return [(x - mean) / std_dev for x in data]


## @brief Method to calculate composite score
## @param returns: list of returns
## @return composite_score: calculated composite score
## @return normalized_returns: normalized returns
## @return normalized_vwap: normalized vwap
## @return normalized_rsi: normalized rsi
def composite_score(returns):
    # Define weights for each metric
    weight_returns = 0.4
    weight_vwap = 0.2
    weight_rsi = 0.4
    normalized_returns = [
        returns["1y"]["return"],
        returns["1mo"]["return"] * 12,
        returns["1w"]["return"] * 52,
    ]
    normalized_vwap = z_score_normalize(
        [returns["1y"]["vwap"], returns["1mo"]["vwap"], returns["1w"]["vwap"]]
    )
    normalized_rsi = z_score_normalize(
        [returns["1y"]["rsi"], returns["1mo"]["rsi"], returns["1w"]["rsi"]]
    )

    # Calculate the composite score
    composite_score = (
        weight_returns * sum(normalized_returns)
        + weight_vwap * sum(normalized_vwap)
        + weight_rsi * sum(normalized_rsi)
    )

    return composite_score, normalized_returns, normalized_vwap, normalized_rsi


## @brief Method to get list of stocks from tickertape
## @param baseUrl: base url to fetch list of stocks
## @return results: list of stocks
def getStockList(
    baseUrl="https://www.tickertape.in/indices/nifty-200-index-.NIFTY200/constituents?type=marketcap",
):
    tickerRequest = TickerRequest()
    res = tickerRequest.get(baseUrl)
    results = []

    if res.ok:
        soup = BeautifulSoup(res.content, features="html.parser")
        mainTable = soup.select_one(".constituent-list-container")
        subTables = mainTable.find_all("div", {"class": "constituent-data-row"})

        def fetch_stock_data(s):
            aTag = s.find("a", href=True)
            sTag = s.find("span", {"class": "typography-caption-medium"})
            apiTicker = aTag["href"].split("-")[-1]
            base_api_url = f"https://api.tickertape.in/stocks/charts/inter/{apiTicker}"
            returns = {}
            current_price = -1.0

            for duration in ["1y", "1mo", "1w"]:
                apiUrl = f"{base_api_url}?duration={duration}"
                logging.info(f"Fetching data for {sTag.text} last {duration}")
                res = tickerRequest.get(apiUrl)

                if res.ok:
                    res_json = res.json()
                    returns[duration] = {"return": res_json["data"][0]["r"]}
                    data_points = res_json["data"][0]["points"]
                    returns[duration]["vwap"] = calculate_vwap(data_points)
                    returns[duration]["rsi"] = calculate_rsi(data_points)

                    if duration == "1w":
                        current_price = data_points[-1]["lp"]
                else:
                    logging.info(f"Failed to get data for {apiTicker}")

            score, ret, v, rsi = composite_score(returns)

            results.append(
                {
                    "stock": aTag.text,
                    "symbol": sTag.text,
                    "returns": returns,
                    "price": current_price,
                    "composite_score": score,
                    "normalized_returns": ret,
                    "normalized_vwap": v,
                    "normalized_rsi": rsi,
                }
            )

        # Use ThreadPoolExecutor for concurrent fetching
        # with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        #     executor.map(fetch_stock_data, subTables)
        for s in subTables:
            fetch_stock_data(s)

        results = sorted(results, key=lambda x: x["composite_score"], reverse=True)
    else:
        logging.info("Failed to get data from %s", baseUrl)
        ### show error message
        logging.info(res.text)
    return results


## @brief Method to display portfolio
## @param data_items: list of stocks
def display_portfolio(data_items):
    N = len(data_items)
    ## display header
    logging.info(
        "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
            "Symbol",
            "Price",
            "1y",
            "1mo",
            "1w",
            "1y_vwap",
            "1mo_vwap",
            "1w_vwap",
            "1y_rsi",
            "1mo_rsi",
            "1w_rsi",
            "Weight",
            "Shares",
            "Investment",
        )
    )
    ## display data
    for stock in data_items[:N]:
        logging.info(
            "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
                stock["symbol"],
                stock["price"],
                round(stock["returns"]["1y"]["return"], 2),
                round(stock["returns"]["1mo"]["return"], 2),
                round(stock["returns"]["1w"]["return"], 2),
                round(stock["returns"]["1y"]["vwap"], 2),
                round(stock["returns"]["1mo"]["vwap"], 2),
                round(stock["returns"]["1w"]["vwap"], 2),
                round(stock["returns"]["1y"]["rsi"], 2),
                round(stock["returns"]["1mo"]["rsi"], 2),
                round(stock["returns"]["1w"]["rsi"], 2),
                round(stock["weight"], 2),
                stock["shares"],
                round(stock["investment"], 2),
            )
        )

    ## calculate total investment
    total = sum([stock["shares"] * stock["price"] for stock in portfolio])
    logging.info(f"Total investment: {total}")


## @brief Method to get file name
## @param prefix: prefix of the file name
## @param days: number of days to subtract from today
## @return fileName: file name
def get_file_name(prefix="stocks-nifty-200", days=0):
    today = datetime.datetime.today()
    if days:
        today = today - datetime.timedelta(days=days)
    return f"{prefix}-{today.strftime('%Y-%m-%d')}.json"


## @brief Method to load portfolio from file - Used for testing only
## @param fileName: file name
## @return portfolio: portfolio
def load_portfolio(fileName):
    portfolio = None
    if pathlib.Path(fileName).exists():
        with open(fileName, "r") as fh:
            portfolio = json.load(fh)
    return portfolio


## @brief Helper method to build portfolio for given number of stocks and investment amount
## @param data_items: list of stocks
## @param N: number of stocks
## @param investment: investment amount
## @return portfolio: portfolio
def build_portfolio(data_items, N=10, investment=100000):
    ## Take top N stocks, clone it
    portfolio = []
    for stock in data_items[:N]:
        portfolio.append(stock.copy())

    ## calculate weight
    for stock in portfolio:
        stock["weight"] = round(100 / N, 2)

    ## calculate number of shares
    for stock in portfolio:
        stock["shares"] = int(investment * stock["weight"] / 100.0 / stock["price"])
        if stock["shares"] == 0:
            raise ValueError(
                "Investment amount is less than price of highest priced stock"
            )
        stock["investment"] = stock["shares"] * stock["price"]

    return portfolio


## @brief Helper method to rebalance portfolio previous day and current day
## @param portfolio_1: previous day portfolio
## @param portfolio_2: current day portfolio
## @return diff_portfolio_info: difference in portfolio
## @return buy_value: buy value
## @return sell_value: sell value
## @return comment: comment
def rebalance_portfolio(portfolio_1, portfolio_2):
    def get_stock_info(portfolio):
        stock_info = {}
        for stock in portfolio:
            stock_info[stock["symbol"]] = {
                "shares": stock["shares"],
                "investment": stock["investment"],
                "price": stock["price"],
            }
        return stock_info

    diff_portfolio_info = {}
    buy_value = 0.0
    sell_value = 0.0
    stock_info_1 = get_stock_info(portfolio_1)
    stock_info_2 = get_stock_info(portfolio_2)

    ## find stock in portfolio_2 but not in portfolio
    for stock in stock_info_2:
        if stock not in stock_info_1:
            diff_portfolio_info[stock] = stock_info_2[stock]["shares"]
            buy_value += stock_info_2[stock]["shares"] * stock_info_2[stock]["price"]

    ## find stock in portfolio but not in portfolio_2

    for stock in stock_info_1:
        if stock not in stock_info_2:
            diff_portfolio_info[stock] = -stock_info_1[stock]["shares"]
            sell_value += stock_info_1[stock]["shares"] * stock_info_1[stock]["price"]

    ## find common stocks
    for stock in stock_info_2:
        if stock in stock_info_1:
            diff_portfolio_info[stock] = (
                stock_info_2[stock]["shares"] - stock_info_1[stock]["shares"]
            )
            if diff_portfolio_info[stock] > 0:
                buy_value += diff_portfolio_info[stock] * stock_info_2[stock]["price"]
            else:
                sell_value += -diff_portfolio_info[stock] * stock_info_1[stock]["price"]

    diff_amount = sell_value - buy_value
    comment = ""
    if diff_amount > 0:
        comment = "Get %.2f" % diff_amount
    else:
        comment = "Invest %.2f" % -diff_amount
    return diff_portfolio_info, buy_value, sell_value, comment


## General testing and simulation
if __name__ == "__main__":
    ## filename : stocks-nifty-200-YYYY-MM-DD.json
    fileName = get_file_name()
    if pathlib.Path(fileName).exists():
        with open(fileName, "r") as fh:
            nifty200_symbols = json.load(fh)
    else:
        nifty200_symbols = getStockList()
        with open(fileName, "w") as fh:
            json.dump(nifty200_symbols, fh, indent=2)
    fileName = get_file_name("portfolio-on")
    portfolio = load_portfolio(fileName)
    if portfolio:
        logging.info("Portfolio loaded from file")
    else:
        portfolio = build_portfolio(
            data_items=nifty200_symbols, N=12, investment=250000
        )
        with open(fileName, "w") as fh:
            json.dump(portfolio, fh, indent=2)
    display_portfolio(portfolio)

    previous_day_file_name = get_file_name("portfolio-on", days=1)
    if pathlib.Path(previous_day_file_name).exists():
        with open(previous_day_file_name, "r") as fh:
            previous_day_portfolio = json.load(fh)
            rebalance = rebalance_portfolio(previous_day_portfolio, portfolio)
            with open(get_file_name("rebalance-on"), "w") as fh:
                json.dump(rebalance, fh, indent=2)
            logging.info(json.dumps(rebalance, indent=2))

    # ## get middle 5 stocks and first 5 stocks and last 5 stocks from nifty200_symbols
    # middle = nifty200_symbols[100:105]
    # first = nifty200_symbols[:8]
    # last = nifty200_symbols[-2:]
    # ## join all 3 lists
    # data_items = middle + first + last
    # portfolio_2 = build_portfolio(data_items=data_items, N=12, investment=1500000)
    # display_portfolio(portfolio_2)
    # diff_portfolio_info, buy_value, sell_value, comment = rebalance_portfolio(
    #     portfolio, portfolio_2
    # )
    # logging.info(json.dumps(diff_portfolio_info, indent=2))
    # logging.info(f"Buy value: {buy_value}")
    # logging.info(f"Sell value: {sell_value}")
    # logging.info(f"Comment: {comment}")
