## Author: Prashant Srivastava

import json
import logging
import sys
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
            # No need to use credentials if you are using public login
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
def composite_score(returns, price):
    # Define weights for each metric
    weight_returns = 0.3  ## weighing 30%  for returns
    weight_vwap = 0.2  ## weighing 20% for vwap
    weight_rsi = 0.5  ## weighing 50% for rsi

    normalized_returns = [
        returns["1y"]["return"],
        100.0 * ((1 + returns["1mo"]["return"] / 100.0) ** 12 - 1),
        100.0 * ((1 + returns["1w"]["return"] / 100.0) ** 52 - 1),
    ]
    ## weighing the recent value more, difference from current price
    weighted_vwap = [0.2, 0.3, 0.5]
    normalized_vwap = [
        (price - returns["1y"]["vwap"]) * weighted_vwap[0] / price,
        (price - returns["1mo"]["vwap"]) * weighted_vwap[1] / price,
        (price - returns["1w"]["vwap"]) * weighted_vwap[2] / price,
    ]

    normalized_rsi = [returns["1y"]["rsi"], returns["1mo"]["rsi"], returns["1w"]["rsi"]]

    # Calculate the composite score
    composite_score_result = (
        weight_returns * sum(normalized_returns)
        + weight_vwap * sum(normalized_vwap)
        + weight_rsi * sum(normalized_rsi)
    )

    return composite_score_result, normalized_returns, normalized_vwap, normalized_rsi


def fetch_nifty_200_data():
    apiTicker = ".NIFTY200"
    base_api_url = f"https://api.tickertape.in/stocks/charts/inter/{apiTicker}"
    tickerRequest = TickerRequest()
    result = {}
    duration = "1d"
    apiUrl = f"{base_api_url}?duration={duration}"
    logging.info(f"Fetching data for {apiTicker} last {duration}")
    try:
        res = tickerRequest.get(apiUrl)
        if res.ok:
            res_json = res.json()
            data_points = res_json["data"][0]["points"]
            result["rsi"] = calculate_rsi(data_points)
            result["current_price"] = data_points[-1]["lp"]
            return result
        else:
            logging.info(f"Reponse failed to get data for {apiTicker}")
    except Exception as e:
        logging.error(e)
        logging.error(f"Failed to get data for {apiTicker}")
    return None


## @brief Method to get list of stocks from tickertape
## @param baseUrl: base url to fetch list of stocks
## @return results: list of stocks
def getStockList(
    baseUrl="https://www.tickertape.in/indices/nifty-200-index-.NIFTY200/constituents?type=marketcap",
):
    tickerRequest = TickerRequest()
    res = tickerRequest.get(baseUrl)
    results = []
    retries = {}
    tickertape_links = {}

    if res.ok:
        soup = BeautifulSoup(res.content, features="html.parser")
        mainTable = soup.select_one(".constituent-list-wrapper")
        if not mainTable:
            logging.info("Failed to get data from %s", baseUrl)
            return results
        subTables = mainTable.find_all("tr", {"class": "constituent-data-row"})

        ## display number of stocks
        logging.info(f"Number of stocks: {len(subTables)}")

        def fetch_stock_data(s, retry=False):
            aTag = s.find("a", href=True)
            sTag = s.find("span", {"class": "typography-caption-medium"})
            apiTicker = aTag["href"].split("-")[-1]
            tickertape_links[sTag.text] = f"https://www.tickertape.in{aTag['href']}"
            base_api_url = f"https://api.tickertape.in/stocks/charts/inter/{apiTicker}"
            returns = {}
            current_price = -1.0

            for duration in ["1y", "1mo", "1w"]:
                apiUrl = f"{base_api_url}?duration={duration}"
                logging.info(f"Fetching data for {sTag.text} last {duration}")
                try:
                    res = tickerRequest.get(apiUrl)

                    if res.ok:
                        res_json = res.json()
                        returns[duration] = {"return": res_json["data"][0]["r"]}
                        data_points = res_json["data"][0]["points"]
                        returns[duration]["vwap"] = calculate_vwap(data_points)
                        returns[duration]["rsi"] = calculate_rsi(data_points)

                        if duration == "1w":
                            current_price = data_points[-1]["lp"]
                        if retry:
                            logging.info(f"Success Retrying {sTag.text} {duration}")
                            retries[s] = 0
                    else:
                        logging.info(f"Reponse failed to get data for {apiTicker}")
                except ValueError as e:
                    loggin.error(f"Failed to get data for {apiTicker} : {e}")
                except Exception as e:
                    logging.error(e)
                    logging.error(f"Failed to get data for {apiTicker}")
                    ## add to retry queue
                    if not retry:
                        retries[s] = 3
                    else:
                        retries[s] -= 1
                        logging.info(
                            f"Again will retry {sTag.text} {retries[s]} time(s)"
                        )
            
            ## if all duration shows up in returns
            if "1y" in returns and "1mo" in returns and "1w" in returns:
                score, ret, v, rsi = composite_score(returns, current_price)
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
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(fetch_stock_data, subTables)
        # for s in subTables:
        #    fetch_stock_data(s)

        ## retry failed requests
        for s in retries:
            if retries[s] > 0:
                fetch_stock_data(s, retry=True)
            else:
                logging.info(f"Failed to fetch data for {s.text} after 3 retries")

        results = sorted(results, key=lambda x: x["composite_score"], reverse=True)
    else:
        logging.info("Failed to get data from %s", baseUrl)
        ### show error message
        logging.info(res.text)
    return results, tickertape_links


## @brief Method to display portfolio
## @param data_items: list of stocks
def display_portfolio(data_items, name="Portfolio"):
    N = len(data_items)
    ## display header
    logging.info(f"{name} ({N} stocks)")
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
    total = sum([stock["shares"] * stock["price"] for stock in data_items])
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
    weight = round(100 / N, 2)
    ## filter out stocks with price greater than investment amount
    data_items = [
        stock
        for stock in data_items
        if int(investment * weight / 100.0 / stock["price"]) > 0
    ]
    for stock in data_items[:N]:
        portfolio.append(stock.copy())

    ## calculate weight
    for stock in portfolio:
        stock["weight"] = weight

    ## calculate number of shares
    for stock in portfolio:
        stock["shares"] = int(investment * stock["weight"] / 100.0 / stock["price"])
        if stock["shares"] == 0:
            raise ValueError(
                "Investment amount is less than price of highest priced stock"
            )
        stock["investment"] = stock["shares"] * stock["price"]

    return portfolio


## @brief Helper method to get price list of stocks
## @param data_items: list of stocks
## @return price_list: price list of stocks
def build_price_list(data_items):
    return {stock["symbol"]: stock["price"] for stock in data_items}


## @brief Helper method to get stock info
## @param portfolio_data: portfolio data
## @return stock_info: stock info
def get_stock_info(portfolio_data):
    stock_info = {}
    for stock in portfolio_data:
        stock_info[stock["symbol"]] = {
            "shares": stock["shares"],
            "investment": stock["investment"],
            "price": stock["price"],
        }
    return stock_info


## @brief Helper method to rebalance portfolio previous day and current day
## @param previous_day_portfolio: previous day portfolio
## @param current_day_portfolio: current day portfolio
## @return current_day_price_dict: latest price of stocks
## @return diff_portfolio_info: difference in portfolio along with capital incurred
def rebalance_portfolio(
    previous_day_portfolio, current_day_portfolio, current_day_price_dict
):
    capital_incurred = 0
    result = {"stocks": [], "capital_incurred": ""}

    day1_stock_info = get_stock_info(previous_day_portfolio)
    day2_stock_info = get_stock_info(current_day_portfolio)
    # Calculate the current value of each stock on Day 2
    for stock, info in day1_stock_info.items():
        shares_day1 = info.get("shares", 0)
        shares_day2 = day2_stock_info.get(stock, {}).get("shares", 0)
        try:
            price_day2 = current_day_price_dict[stock]
        except KeyError:
            logging.warning("Price not available for %s", {stock})
            price_day2 = info.get(
                "price", 0
            )  ## use previous day price if not available
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
    ##  so that the "no change" items come first, followed by "sold" items, and then "bought" items,
    ## and then at last sort by symbol
    result["stocks"] = sorted(
        result["stocks"],
        key=lambda x: (x["shares"] == 0, x["shares"] < 0, x["symbol"]),
        reverse=True,
    )
    result["capital_incurred"] = capital_incurred
    return result


## General testing and simulation
if __name__ == "__main__":
    date_provided = len(sys.argv) == 2
    if date_provided:
        logging.info(f"Date provided: {sys.argv[1]}")
        fileName = f"nifty200-symbols-{sys.argv[1]}.json"
    ## filename : stocks-nifty-200-YYYY-MM-DD.json
    else:
        fileName = get_file_name()
    if pathlib.Path(fileName).exists():
        with open(fileName, "r") as fh:
            nifty200_symbols = json.load(fh)
    else:
        logging.info("File not found: %s, fetching data from tickertape", fileName)
        nifty200_symbols, tickertape_links = getStockList()
        with open(fileName, "w") as fh:
            json.dump(nifty200_symbols, fh, indent=2)
        with open("tickertape_links.json", "w") as fh:
            json.dump(tickertape_links, fh, indent=2)
    if date_provided:
        fileName = f"portfolio-on-{sys.argv[1]}.json"
    else:
        fileName = get_file_name("portfolio-on")
    portfolio = load_portfolio(fileName)
    if portfolio:
        logging.info("Portfolio loaded from file")
    else:
        portfolio = build_portfolio(
            data_items=nifty200_symbols, N=15, investment=500000
        )
        with open(fileName, "w") as fh:
            json.dump(portfolio, fh, indent=2)
    display_portfolio(portfolio, "Today's Portfolio")

    previous_day_file_name = get_file_name("portfolio-on", days=1)
    if pathlib.Path(previous_day_file_name).exists():
        with open(previous_day_file_name, "r") as fh:
            previous_day_portfolio = json.load(fh)
            display_portfolio(previous_day_portfolio, "Previous Day Portfolio")
            if date_provided:
                rebalance_file_name = f"rebalance-on-{sys.argv[1]}.json"
            else:
                rebalance_file_name = get_file_name("rebalance-on")
            if True or not pathlib.Path(rebalance_file_name).exists():
                rebalance = rebalance_portfolio(
                    previous_day_portfolio,
                    portfolio,
                    build_price_list(nifty200_symbols),
                )
                with open(rebalance_file_name, "w") as fh:
                    json.dump(rebalance, fh, indent=2)
            else:
                logging.info("Rebalance file already exists")
                rebalance = json.load(open(rebalance_file_name, "r"))
            logging.info(json.dumps(rebalance, indent=2))
