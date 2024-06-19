"""Parallel web scraper for stock news from MoneyControl."""

import argparse
import json
import logging
import os
import csv
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    ## pylint: disable=line-too-long
    format="%(asctime)s [%(levelname)s] %(name)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Set logging level for `requests` to WARNING to suppress DEBUG logs
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


class StockNewsScraper:
    """Scraper for stock news from MoneyControl."""

    BASE_URL = "https://www.moneycontrol.com/news/tags/recommendations.html"

    def __init__(self, back_days=0):
        self.stock_news = []
        self.back_days = back_days

    def fetch_page(self, url):
        """Fetches the content of a webpage."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as error:
            logging.error("Error fetching %s: %s", url, error)
            return None

    def parse_article(self, url):
        """Parses details from the article page."""
        content = self.fetch_page(url)
        if content is None:
            return None

        soup = BeautifulSoup(content, "html.parser")
        try:
            summary = soup.select_one(".article_desc").get_text(strip=True)
            published_date = soup.select_one(".tags_last_line").get_text(strip=True)
            published_date = datetime.datetime.strptime(
                published_date, "first published: %b %d, %Y %I:%M %p"
            )
            paragraphs = [
                para.get_text(strip=True) for para in soup.select("#contentdata > p")
            ]
            ## take only first 2 paragraphs
            paragraphs = paragraphs[:2]
            ## summary has ".+target price of Rs XYZ.+" and we need to extract the target price
            regex = r".+target price of Rs (\S+)\s+.+"
            target_price = None
            if (match := re.match(regex, summary)) is not None:
                target_price = match.group(1)

            # paragraphs_href = [
            #     para.get("href")
            #     for para in soup.select("#contentdata > p > strong > a")
            # ][0]
            # content = self.fetch_page(paragraphs_href)
            # stock_name = None
            # if content:
            #     child_soup = BeautifulSoup(content, "html.parser")
            #     stock_name = child_soup.select_one("#stockName > h1").get_text(
            #         strip=True
            #     )
            tags = [
                tag.get_text(strip=True) for tag in soup.select(".tags_first_line > a")
            ]
            content = {
                "summary": summary,
                # "stock_name": stock_name,
                "published_date": published_date.strftime("%Y-%m-%d %H:%M:%S"),
                "paragraphs": paragraphs,
                "tags": tags,
                "target_price": target_price,
            }
            return content
        except AttributeError as error:
            logging.error("Error parsing article %s: %s", url, error)
            return None
        except Exception as error:  # pylint: disable=broad-except
            logging.error("Error processing article %s: %s", url, error)
            return None

    def parse_main_page(self, content):
        """Parses the main page to get entry links and details."""
        soup = BeautifulSoup(content, "html.parser")
        entries = soup.select("#t_top > #cagetory > li")
        entry_data = []
        todays_date = datetime.datetime.now().date()
        for entry in entries:
            try:
                published_date = entry.select_one("span").get_text(strip=True)
                # parse the date string into a datetime object, format is June 12, 2024 01:49 PM IST
                published_date = datetime.datetime.strptime(
                    published_date, "%B %d, %Y %I:%M %p IST"
                )
                jump_page = entry.select_one("h2 > a")["href"]
                ## difference between published_date and todays date should be less than back_days
                if (todays_date - published_date.date()).days > self.back_days:
                    logging.debug(
                        "Skipping entry from %s for news article on %s",
                        published_date,
                        jump_page,
                    )
                    continue
                # If timezone information is important, consider parsing and handling it separately

                news_heading = entry.select_one("h2 > a").get_text(strip=True)
                entry_data.append((published_date, jump_page, news_heading))
            except AttributeError as error:
                logging.error("Error parsing entry: %s", error)
            except Exception as error:  # pylint: disable=broad-except
                logging.error("Error processing entry: %s", error)
        return entry_data

    def scrape(self):
        """Main method to scrape the stock news."""
        content = self.fetch_page(self.BASE_URL)
        if content is None:
            return None

        entries = self.parse_main_page(content)
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future_to_entry = {
                executor.submit(self.parse_article, entry[1]): entry
                for entry in entries
            }
            for future in tqdm(
                as_completed(future_to_entry),
                total=len(future_to_entry),
                desc="Processing articles",
            ):
                entry = future_to_entry[future]
                try:
                    article_info = future.result()
                    if article_info:
                        self.stock_news.append(
                            {
                                "published_date": entry[0],
                                "url": entry[1],
                                "broker": entry[2].split(":")[-1],
                                "recommendation": entry[2].split(":")[0].split(" ")[0],
                                "stock": " ".join(
                                    entry[2].split(";")[0].split(" ")[1:]
                                ),
                            }
                        )
                except Exception as error:  # pylint: disable=broad-except
                    logging.error("Error processing entry %s: %s", entry, error)

        return self.stock_news


def get_stock_news(back_days=1):
    """Get stock news from MoneyControl."""
    scraper = StockNewsScraper(back_days)
    return scraper.scrape()


def main(back_days):
    """Main entry point of the script."""
    scraper = StockNewsScraper(back_days)
    news = scraper.scrape()
    # Output or further processing of stock_news
    with open("stock_news.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(news, indent=2))

    ## write to csv following the format with header
    ## Stock Name, Broker, Recommendation, Target Price, Published Date
    ## use csv module to write to csv

    with open("stock_news.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "Stock Name",
                "Broker",
                "Recommendation",
                "Target Price",
                "Published Date",
                "URL",
            ]
        )
        for news_item in news:
            writer.writerow(
                [
                    news_item["stock"],
                    news_item["broker"],
                    news_item["recommendation"],
                    news_item["target_price"],
                    news_item["published_date"],
                    news_item["url"],
                ]
            )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--back-days",
        type=int,
        default=1,
        help="Number of days to go back to fetch the news",
    )
    args = parser.parse_args()
    main(args.back_days)
