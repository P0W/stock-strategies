import requests
import logging
import concurrent.futures
from bs4 import BeautifulSoup
import json
from tqdm import tqdm


def score_stock(score_card):
    """Score a stock based on its score card.
    The score card is a dictionary with the following keys:
    - Performance
    - Growth
    - Profitability
    - Valuation
    - Entry point
    - Red flags
    """
    fields = {
        "Performance": 5,
        "Growth": 5,
        "Profitability": 5,
        "Valuation": 4,
        "Entry point": 3,
        "Red flags": 1,
    }
    colors = {"green": 2, "yellow": 1, "red": -2}
    score = 0
    for field, weight in fields.items():
        color = score_card.get(field)
        if color:
            score += weight * colors[color]
    return score


## @brief Method to get list of stocks from tickertape
## @param baseUrl: base url to fetch list of stocks
## @return results: list of stocks
def getStockList(
    baseUrl="https://www.tickertape.in/indices/nifty-200-index-.NIFTY200/constituents?type=marketcap",
):
    res = requests.get(baseUrl)
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
            tLink = f"https://www.tickertape.in{aTag['href']}"
            tickertape_links[sTag.text] = tLink
            base_api_url = (
                f"https://analyze.api.tickertape.in/stocks/scorecard/{apiTicker}"
            )
            score_card = []
            composite_score = 0
            # logging.info(f"Fetching data for {sTag.text}")
            try:
                res = requests.get(base_api_url)

                if res.ok:
                    res_json = res.json()
                    score_card = {
                        item["name"]: item["colour"] for item in res_json["data"]
                    }
                    composite_score = score_stock(score_card)
                else:
                    logging.info(f"Reponse failed to get data for {apiTicker}")
            except Exception as e:
                logging.error(e)
                logging.error(f"Failed to get data for {apiTicker}")
                ## add to retry queue
                if not retry:
                    retries[s] = 3
                else:
                    retries[s] -= 1
                    logging.info(f"Again will retry {sTag.text} {retries[s]} time(s)")

            results.append(
                {
                    "stock": aTag.text,
                    "symbol": sTag.text,
                    "score_card": score_card,
                    "link": tLink,
                    "composite_score": composite_score,
                }
            )

        # Use ThreadPoolExecutor for concurrent fetching
        with concurrent.futures.ThreadPoolExecutor() as executor:
            list(tqdm(executor.map(fetch_stock_data, subTables), total=len(subTables)))
        ## retry failed requests
        for s in retries:
            if retries[s] > 0:
                fetch_stock_data(s, retry=True)
            else:
                logging.info(f"Failed to fetch data for {s.text} after 3 retries")
    else:
        logging.info("Failed to get data from %s", baseUrl)
        ### show error message
        logging.info(res.text)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stocks = getStockList()
    ## sort by composite score
    stocks = sorted(stocks, key=lambda x: x["composite_score"], reverse=True)
    ## print top 10 stocks
    for stock in stocks[:15]:
        print(json.dumps(stock, indent=2))

    ## create a csv file
    with open("scorecard.csv", "w") as f:
        f.write("Stock,Symbol,Composite Score,Link\n")
        for stock in stocks:
            f.write(
                f"{stock['stock']},{stock['symbol']},{stock['composite_score']},{stock['link']}\n"
            )
