export type ItemType = string | number;

export interface IHeader {
    display: string;
    key: string;
    cellTemplate?: (item: ItemType, row?: IStockData | IRebalanceData | INifty200Data) => React.ReactElement | null;
}

export interface IStockTable {
    headers: IHeader[];
    stockData: IStockData[] | IRebalanceData[] | INifty200Data[];
}

export interface ITickerTapeLinks {
    [key: string]: any;
}

export interface IStockData {
    [key: string]: any;
    stock: string;
    symbol: string;
    price: number;
    weight: number;
    shares: number;
    investment: number;
    composite_score: number;

    returns: {
        [key: string]: any;
        '1y': {
            return: number;
            vwap: number;
            rsi: number;
        },
        '1mo': {
            return: number;
            vwap: number;
            rsi: number;
        },
        '1w': {
            return: number;
            vwap: number;
            rsi: number;
        }
    }
};

export interface IPortfolio {
    tickertape_links: ITickerTapeLinks;
    portfolio: IStockData[];
}

export interface IRebalanceData {
    [key: string]: any;
    symbol: string;
    amount: number;
    shares: number;
    stock: string;
    url: string;
    initial_shares: number;
};

export interface INifty200Data {
    [key: string]: any;
    symbol: string;
    price: number;
};

export interface IToFromData extends INifty200Data {
    avg_price: number;
    shares: number;
    stock: string;
    investment: number;
    weight: number;
    url: string;
};


export interface ISymbolRow {
    rank: number;
    item: IStockData | IRebalanceData | INifty200Data;
    headers: IHeader[];
};

/**
 * "stock": "Indian Oil Corporation Ltd",
  "symbol": "IOC",
  "score_card": {
    "Performance": "yellow",
    "Valuation": "green",
    "Growth": "red",
    "Profitability": "green",
    "Entry point": "green",
    "Red flags": "green"
  },
  "link": "https://www.tickertape.in/stocks/indian-oil-corporation-IOC",
  "composite_score": 23
}
 */
export interface IStockBalls {
    stock: string;
    symbol: string;
    score_card: {
        [key: string]: string;
    };
    link: string;
    composite_score: number;
};
