"""Generates valuation scores for stocks in the Nifty 200 index."""
import logging
import concurrent.futures
import json
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

##pylint: disable=invalid-name


def score_stock(score_card):
    """Score a stock based on its score card.
    The score card is a dictionary with the following keys:
    - Performance
    - Growth
    - Profitability
    - Valuation
    - Entry point
    - Red flags
    Growth > Performance > Profitability > Valuation > Entry point > Red flags
    """
    fields = {
        "Growth": 0.3,  # 30% weight to Growth
        "Performance": 0.25,  # 25% weight to Performance
        "Profitability": 0.2,  # 20% weight to Profitability
        "Valuation": 0.15,  # 15% weight to Valuation
        "Entry point": 0.07,  # 7% weight to Entry point
        "Red flags": 0.03,  # 3% weight to Red flags
    }
    colors = {"green": 0.5, "yellow": 0.3, "red": -0.4}
    score = 0
    for field, weight in fields.items():
        color = score_card.get(field)
        if color:
            score += weight * colors[color]
    return score


### @brief Method to fetch multiple urls using a single session
### @param urls: list of urls to fetch
### @return list of responses
def fetch_all(urls):
    """Fetch multiple URLs using a single session."""
    with requests.Session() as session:
        with ThreadPoolExecutor() as executor:
            return list(executor.map(session.get, urls))


## @brief Method to get list of stocks from tickertape
## @param baseUrl: base url to fetch list of stocks
## @return results: list of stocks
## pylint:disable=too-many-statements,line-too-long
def getStockList(
    baseUrl="https://www.tickertape.in/indices/nifty-200-index-.NIFTY200/constituents?type=marketcap",
):
    """Web scrapper"""
    res = requests.get(baseUrl, timeout=10)
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

        def fetch_stock_data(s, retry=False):
            aTag = s.find("a", href=True)
            sTag = s.find("span", {"class": "typography-caption-medium"})
            apiTicker = aTag["href"].split("-")[-1]
            tLink = f"https://www.tickertape.in{aTag['href']}"
            tickertape_links[sTag.text] = tLink
            base_api_url = (
                f"https://analyze.api.tickertape.in/stocks/scorecard/{apiTicker}"
            )
            price_url = (
                f"https://api.tickertape.in/stocks/charts/inter/{apiTicker}?duration=1w"
            )
            score_card = []
            composite_score = 0
            price = 0
            try:
                res = fetch_all([base_api_url, price_url])
                if res[0].ok:
                    res_json = res[0].json()
                    score_card = {
                        item["name"]: item["colour"] for item in res_json["data"]
                    }
                    composite_score = score_stock(score_card)
                else:
                    logging.info("Reponse failed to get data for %s", apiTicker)
                if res[1].ok:
                    price_data = res[1].json()
                    ## add price data
                    price = price_data["data"][0]["points"][-1]["lp"]
            except Exception as e:  ##pylint: disable=broad-exception-caught
                logging.error(e)
                logging.error("Failed to get data for %s", apiTicker)
                ## add to retry queue
                if not retry:
                    retries[s] = 3
                else:
                    retries[s] -= 1
                    logging.info(
                        "Again will retry %s %d time(s)", sTag.text, retries[s]
                    )

            results.append(
                {
                    "stock": aTag.text,
                    "symbol": sTag.text,
                    "score_card": score_card,
                    "link": tLink,
                    "composite_score": composite_score,
                    "price": price,
                }
            )

        # Use ThreadPoolExecutor for concurrent fetching
        with concurrent.futures.ThreadPoolExecutor() as executor:
            list(tqdm(executor.map(fetch_stock_data, subTables), total=len(subTables)))
        ## retry failed requests
        for key, value in retries.items():
            if value > 0:
                fetch_stock_data(key, retry=True)
            else:
                logging.info("Failed to fetch data for %s after 3 retries", key.text)
    else:
        logging.info("Failed to get data from %s", baseUrl)
        ### show error message
        logging.info(res.text)
    ## sort by composite score, if same use price lower first
    results.sort(key=lambda x: (x["composite_score"], -x["price"]), reverse=True)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stocks = getStockList()
    ## print top 10 stocks
    with open("score.card.json", "w", encoding="utf-8") as f:
        json.dump(stocks[:10], f, indent=2)

    ## create a csv file
    with open("scorecard.csv", "w", encoding="utf-8") as f:
        f.write("Stock,Symbol,Composite Score,Link\n")
        for stock in stocks:
            f.write(
                f"{stock['stock']},{stock['symbol']},{stock['composite_score']},{stock['link']}\n"
            )
