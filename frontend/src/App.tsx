import "./App.css";
import React from 'react';

import { StockTable } from './StockTable';
import { StockDatePicker } from './StockDatePicker';


import { mainTableHeader, nifty200TableHeader, rebalanceTableHeader } from './StockTableHeader';
import { round_off } from './Utils';
import { INifty200Data, IRebalanceData, IStockData, IToFromData } from "./StockDataTypes";

const useData = (toDateString: string, fromDateString: string, numStocks: number, investmentValue: number) => {
  const [toDateStocks, setToDateStocks] = React.useState<IStockData[]>([]);
  const [fromDateStocks, setFromDateStocks] = React.useState<IStockData[]>([]);
  const [currentPrices, setCurrentPrices] = React.useState<INifty200Data[]>([]);
  const [rebalanceData, setRebalanceData] = React.useState<IRebalanceData[]>([]);
  const [capitalIncurred, setCapitalIncurred] = React.useState<number>(0);
  const [loading, setLoading] = React.useState(true);
  const cache = React.useRef<{ [key: string]: IStockData[] }>({});

  const fetchData = async (endpoint: string) => {
    //const urlEndPoint = toDate ? `/${endpoint}/${fromDate}/${toDate}` : `/${endpoint}/${fromDate}/${numStocks}/${investmentValue}`;
    if (cache.current[endpoint]) {
      return Promise.resolve(cache.current[endpoint]);
    } else {
      const res = await fetch(endpoint);
      const data = await res.json();
      cache.current[endpoint] = data;
      return data;
    }
  };


  React.useEffect(() => {
    if (!fromDateString || !toDateString) return;
    setLoading(true);
    const toFetch = fetchData(`/portfolio/${toDateString}/${numStocks}/${investmentValue}`);
    const fromFetch = fetchData(`/portfolio/${fromDateString}/${numStocks}/${investmentValue}`);
    const nifty200Fetch = fetchData(`/nifty200/${toDateString}`);
    const rebalanceFetch = fetchData(`/rebalance/${fromDateString}/${toDateString}`);

    Promise.all([toFetch, fromFetch, rebalanceFetch, nifty200Fetch])
      .then(data => {
        const pastStocksData = data[1] as IStockData[];
        const presentStocksData = data[0] as IStockData[];
        const rebalanceStocksData = data[2] as unknown as { [key: string]: any };
        const nifty200 = data[3] as { [key: string]: number };

        // get the prices for the stocks in the fromDateStocks from nifty200
        const currentStockPrice = pastStocksData.map(stock => {
          const thisStock = Object.keys(nifty200)?.find(niftyStock => niftyStock === stock.symbol);
          if (thisStock) {
            return {
              symbol: stock.symbol,
              price: nifty200[thisStock],
              avg_price: stock.price,
              shares: stock.shares
            } as INifty200Data;
          }
          return { symbol: stock.symbol, price: -1, avg_price: stock.price } as INifty200Data;
        });

        // Set states
        setFromDateStocks(pastStocksData);
        setToDateStocks(presentStocksData);
        setRebalanceData(rebalanceStocksData["stocks"] as IRebalanceData[]);
        setCapitalIncurred(rebalanceStocksData["capital_incurred"]);
        setCurrentPrices(currentStockPrice);
        setLoading(false);
      })
      .catch(err => {
        console.log(err);
        setLoading(false);
      });
  }, [fromDateString, toDateString]);

  return { toDateStocks, fromDateStocks, rebalanceData, capitalIncurred, currentPrices, loading };
};

export const App = () => {
  const [fromDateString, setFromDateString] = React.useState<string>('');
  const [toDateString, setToDateString] = React.useState<string>('');
  const [numStocks, setNumStocks] = React.useState<number>(15);
  const [investmentValue, setInvestmentValue] = React.useState<number>(500000);

  const { toDateStocks, fromDateStocks, rebalanceData, capitalIncurred, currentPrices, loading }
    = useData(toDateString, fromDateString, numStocks, investmentValue);
  // Sum up the investment amount
  const fromInvestment = fromDateStocks.reduce((acc, stock) => acc + stock.investment, 0);
  const toInvestment = toDateStocks.reduce((acc, stock) => acc + stock.investment, 0);
  const currentPortfolioValue = (currentPrices as IToFromData[]).reduce((acc, stock) => acc + stock.shares * stock.price, 0);

  return (
    <div className="App">
      <h4> Nifty-200 Momentum Strategy Analyzer</h4>
      <div className="date-picker-container">
        <label>From:</label>
        <StockDatePicker initialDate={fromDateString} onDateChange={setFromDateString} />
        <label>To:</label>
        <StockDatePicker initialDate={toDateString} onDateChange={setToDateString} />
        <label>Number of Stocks:</label>
        <input type="number" min="1" max="20" defaultValue={numStocks} onChange={(e) => setNumStocks(Number(e.target.value))} />
        <label>Investment Value:</label>
        <input type="number" min="100000" max="1500000" defaultValue={investmentValue} onChange={(e) => setInvestmentValue(Number(e.target.value))} />
      </div>
      {!loading ?
        <div>
          <div style={{ display: 'flex' }}>
            <div className='stock-table-container'>
              <label className="portfolio-value">Investment: {round_off(fromInvestment)} INR | as on {fromDateString}</label>
              <StockTable headers={mainTableHeader} stockData={fromDateStocks} />
            </div>
            <div className='stock-table-container'>
              <label className="portfolio-value">Current: {round_off(currentPortfolioValue)} INR | as on {toDateString}</label>
              <StockTable headers={nifty200TableHeader} stockData={currentPrices} />
            </div>
            <div className='stock-table-container'>
              <label className="portfolio-value">New Investment: {round_off(toInvestment)} INR | as on {toDateString}</label>
              <StockTable headers={mainTableHeader} stockData={toDateStocks} />
            </div>
            <div className='stock-table-container'>
              <label className='portfolio-value'> Rebalance Updates | Capital Incurred: {round_off(capitalIncurred)} INR</label>
              <StockTable headers={rebalanceTableHeader} stockData={rebalanceData} />
            </div>
          </div>

        </div> : fromDateString != '' && toDateString != '' && <div> Loading... </div>
      }
    </div>
  );
};

