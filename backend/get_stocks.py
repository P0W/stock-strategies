## Author: Prashant Srivastava

import json
import logging
import sys
import pathlib
import datetime
import concurrent.futures
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

import requests
from bs4 import BeautifulSoup


logging.basicConfig(
    level=logging.INFO,
    ## pylint: disable=line-too-long
    format="%(asctime)s [%(levelname)s] %(name)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)


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
    if not data:
        return []

    mean = sum(data) / len(data)

    # Calculate standard deviation - handle case where all values are identical
    squared_diffs = [(x - mean) ** 2 for x in data]
    std_dev = (sum(squared_diffs) / len(data)) ** 0.5

    # Avoid division by zero if standard deviation is zero
    if std_dev == 0:
        return [0] * len(data)

    return [(x - mean) / std_dev for x in data]


def _rsi_tent(rsi):
    """Tent function: rewards healthy uptrend RSI (50-65), penalizes overbought (>75).
    Returns ~[-1, 1] range centered around 0."""
    if rsi <= 30:
        return -1.0 + (rsi / 30.0) * 0.5
    elif rsi <= 50:
        return -0.5 + (rsi - 30) / 20.0 * 0.5
    elif rsi <= 65:
        return (rsi - 50) / 15.0
    elif rsi <= 80:
        return 1.0 - (rsi - 65) / 15.0 * 1.5
    else:
        return -0.5 - (rsi - 80) / 20.0 * 0.5


def _raw_components(returns, price):
    """Compute raw time-weighted components for a single stock.
    Bug fixes applied:
    1. VWAP: single time-weight (no double-weighting)
    2. Returns: raw %, NOT annualized for 1w/1mo
    3. RSI: tent function (rewards 50-65, penalizes >75)
    4. Time weights: 1w reduced from 0.50 to 0.25
    """
    time_weights = [0.35, 0.40, 0.25]  # 1y, 1mo, 1w

    raw_returns = [
        returns["1y"]["return"],
        returns["1mo"]["return"],
        returns["1w"]["return"],
    ]

    pct_off_vwap = [
        (price - returns["1y"]["vwap"]) / price * 100.0,
        (price - returns["1mo"]["vwap"]) / price * 100.0,
        (price - returns["1w"]["vwap"]) / price * 100.0,
    ]

    rsi_tented = [
        _rsi_tent(returns["1y"]["rsi"]),
        _rsi_tent(returns["1mo"]["rsi"]),
        _rsi_tent(returns["1w"]["rsi"]),
    ]

    r = sum(x * w for x, w in zip(raw_returns, time_weights))
    v = sum(x * w for x, w in zip(pct_off_vwap, time_weights))
    s = sum(x * w for x, w in zip(rsi_tented, time_weights))
    return r, v, s, raw_returns, pct_off_vwap, rsi_tented


def compute_composite_scores(results):
    """Cross-sectional z-score normalization across the universe,
    then blend with 0.4/0.3/0.3 weights so the labels mean what they say."""
    weight_returns = 0.4
    weight_vwap = 0.3
    weight_rsi = 0.3

    # Phase 1: compute raw components for each stock
    components = []
    for s in results:
        try:
            r, v, rs, raw_ret, raw_vwap, raw_rsi = _raw_components(
                s["returns"], s["price"]
            )
            components.append((r, v, rs))
            s["_raw"] = (r, v, rs)
            s["normalized_returns"] = raw_ret
            s["normalized_vwap"] = raw_vwap
            s["normalized_rsi"] = raw_rsi
        except Exception:
            components.append(None)
            s["_raw"] = None

    # Phase 2: z-score normalize across the universe
    valid = [c for c in components if c is not None]
    if not valid:
        for s in results:
            s["composite_score"] = 0
        return

    r_vals = [c[0] for c in valid]
    v_vals = [c[1] for c in valid]
    s_vals = [c[2] for c in valid]

    def _stats(vals):
        m = sum(vals) / len(vals)
        sd = (sum((x - m) ** 2 for x in vals) / len(vals)) ** 0.5
        return m, sd if sd > 0 else 1.0

    mr, sdr = _stats(r_vals)
    mv, sdv = _stats(v_vals)
    ms, sds = _stats(s_vals)

    for s in results:
        raw = s.pop("_raw", None)
        if raw is None:
            s["composite_score"] = 0
            continue
        zr = (raw[0] - mr) / sdr
        zv = (raw[1] - mv) / sdv
        zs = (raw[2] - ms) / sds
        s["composite_score"] = weight_returns * zr + weight_vwap * zv + weight_rsi * zs


def composite_score(returns, price):
    """Legacy per-stock scoring (used by regenrate_stock_list).
    Applies bug fixes but without cross-sectional z-score normalization."""
    r, v, rs, raw_ret, raw_vwap, raw_rsi = _raw_components(returns, price)

    weight_returns = 0.4
    weight_vwap = 0.3
    weight_rsi = 0.3

    score = weight_returns * r + weight_vwap * v + weight_rsi * rs
    return score, raw_ret, raw_vwap, raw_rsi


## @brief Method to fetch nifty 200 data
## @return result: nifty 200 data
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

        def fetch_stock_data(s):
            aTag = s.find("a", href=True)
            sTag = s.find("span", {"class": "typography-caption-medium"})
            apiTicker = aTag["href"].split("-")[-1]
            tickertape_links[sTag.text] = f"https://www.tickertape.in{aTag['href']}"
            base_api_url = f"https://api.tickertape.in/stocks/charts/inter/{apiTicker}"
            returns = {}
            current_price = -1.0

            # Define fetch function with retries
            @retry(
                stop=stop_after_attempt(4),  # Stop after 4 attempts
                wait=wait_exponential(
                    multiplier=1, min=1, max=10
                ),  # Wait 1, 2, 4, 8 seconds between retries
                retry=retry_if_exception_type(
                    (requests.exceptions.RequestException, ValueError)
                ),
                before_sleep=lambda retry_state: logging.info(
                    f"Retrying {sTag.text} after {retry_state.outcome.exception()} - "
                    f"Attempt {retry_state.attempt_number}"
                ),
            )
            def fetch_duration_data(duration):
                apiUrl = f"{base_api_url}?duration={duration}"
                logging.info(f"Fetching data for {sTag.text} last {duration}")

                res = tickerRequest.get(apiUrl)
                if not res.ok:
                    raise requests.exceptions.RequestException(
                        f"Failed with status {res.status_code}"
                    )

                res_json = res.json()
                result = {"return": res_json["data"][0]["r"]}
                data_points = res_json["data"][0]["points"]
                result["vwap"] = calculate_vwap(data_points)
                result["rsi"] = calculate_rsi(data_points)

                return result, data_points[-1]["lp"] if duration == "1w" else None

            # Fetch data for each duration
            for duration in ["1y", "1mo", "1w"]:
                try:
                    result, price = fetch_duration_data(duration)
                    returns[duration] = result
                    if price is not None:
                        current_price = price
                except Exception as e:
                    logging.error(
                        f"Failed to get data for {sTag.text} {duration} after all retries: {e}"
                    )
                    continue

            # If all durations were successfully fetched
            if "1y" in returns and "1mo" in returns and "1w" in returns:
                results.append(
                    {
                        "stock": aTag.text,
                        "symbol": sTag.text,
                        "returns": returns,
                        "price": current_price,
                    }
                )

        # Use ThreadPoolExecutor for concurrent fetching
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(fetch_stock_data, subTables)

        # Cross-sectional z-score normalization across the universe
        compute_composite_scores(results)

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


## Get the stcok-nifty-200-YYYY-MM-DD.json file from the tickertape
## and calculate the normalized returns, vwap and rsi for each stock
## and then calculate the composite score for each stock
def regenrate_stock_list(fileName):
    with open(fileName, "r") as fh:
        nifty200_symbols = json.load(fh)

    ## cross-sectional z-score normalization across the universe
    compute_composite_scores(nifty200_symbols)

    ## sort the stocks based on the composite score
    nifty200_symbols = sorted(
        nifty200_symbols, key=lambda x: x["composite_score"], reverse=True
    )
    with open("nifty200-symbols-regenrated.json", "w") as fh:
        json.dump(nifty200_symbols, fh, indent=2)
    return nifty200_symbols


## General testing and simulation
if __name__ == "__main__":
    # fileName = "stocks-nifty-200-2025-04-11.json"

    ## Regenerate the stock list
    # regenrate_stock_list(fileName)
    # sys.exit(0)

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
