import { IHeader, StockTable } from './StockTable';
import { StockDatePicker } from './StockDatePicker';
import "./App.css";
import React from 'react';
import { IRebalanceData, IStockData } from './SymbolRow';


// Round to 2 decimal places
const round_off = (num: number): number => {
  return Math.round(num * 100) / 100;
}

const ReturnsTemplate = (item: number) => {
  return <td className="returns">{round_off(item)}</td>;
};

const mainTableHeader: IHeader[] = [
  {
    display: 'S.No.',
    key: 'rank'
  },
  {
    display: 'Stock',
    key: 'stock'
  },
  {
    display: 'Symbol',
    key: 'symbol'
  },
  {
    display: 'Price',
    key: 'price'
  },
  {
    display: 'Weight',
    key: 'weight'
  },
  {
    display: 'Shares',
    key: 'shares'
  },
  {
    display: 'Investment',
    key: 'investment'
  },
  {
    display: 'Score',
    key: 'composite_score',
    cellTemplate: (item: number) => <td>{round_off(item)}</td>
  }
];

const rebalanceTableHeader: IHeader[] = [
  {
    display: 'S.No.',
    key: 'rank'
  },
  {
    display: 'Symbol',
    key: 'symbol'
  },
  {
    display: 'Amount',
    key: 'amount'
  },
  {
    display: 'Shares',
    key: 'shares'
  },
  {
    display: 'Action',
    key: 'shares',
    cellTemplate: (item: number) => <td>{item === 0 ? 'Hold' : (item > 0 ? 'Buy' : 'Sell')}</td>
  }
];

const useData = (toDateString: string, fromDateString: string) => {
  const [toDateStocks, setToDateStocks] = React.useState<IStockData[]>([]);
  const [fromDateStocks, setFromDateStocks] = React.useState<IStockData[]>([]);
  const [rebalanceData, setRebalanceData] = React.useState<IRebalanceData[]>([]);
  const [capitalIncurred, setCapitalIncurred] = React.useState<number>(0);
  const [loading, setLoading] = React.useState(true);
  const cache = React.useRef<{ [key: string]: IStockData[] }>({});

  const fetchData = async (endpoint: string, fromDate: string, toDate?: string) => {
    const urlEndPoint = toDate ? `/${endpoint}/${fromDate}/${toDate}` : `/${endpoint}/${fromDate}`;
    if (cache.current[urlEndPoint]) {
      return Promise.resolve(cache.current[urlEndPoint]);
    } else {
      const res = await fetch(urlEndPoint);
      const data = await res.json();
      cache.current[urlEndPoint] = data;
      return data;
    }
  };


  React.useEffect(() => {
    setLoading(true);
    const toFetch = fetchData('portfolio', toDateString);
    const fromFetch = fetchData('portfolio', fromDateString);
    const nifty200Fetch = fetchData('nifty200', toDateString);
    const rebalanceFetch = fetchData('rebalance', toDateString, fromDateString);

    Promise.all([toFetch, fromFetch, nifty200Fetch, rebalanceFetch])
      .then(data => {
        setToDateStocks(data[0][0]);
        setFromDateStocks(data[1][0]);
        setRebalanceData(data[3]["stocks"]);
        setCapitalIncurred(data[3]["capital_incurred"]);
        setLoading(false);
      })
      .catch(err => {
        console.log(err);
        setLoading(false);
      });
  }, [toDateString, fromDateString]);

  return { toDateStocks, fromDateStocks, rebalanceData, capitalIncurred, loading };
};

export const App = () => {
  const [toDateString, setToDateString] = React.useState<string>('2023-10-04');
  const [fromDateString, setFromDateString] = React.useState<string>('2023-10-04');

  const { toDateStocks, fromDateStocks, rebalanceData, capitalIncurred, loading } = useData(toDateString, fromDateString);

  // Sum up the investment amount
  const totalInvestment = toDateStocks.reduce((acc, stock) => acc + stock.investment, 0);

  return (
    <div className="App">
      <div className="date-picker-container">
        <label>From:</label>
        <StockDatePicker onDateChange={setFromDateString} />
        <label>To:</label>
        <StockDatePicker onDateChange={setToDateString} />
      </div>
      {!loading ?
        <div> <StockTable headers={mainTableHeader} stockData={toDateStocks} />
          <h3> Total Investment: {round_off(totalInvestment)} INR</h3>
          <h1> Rebalances</h1>
          <StockTable headers={rebalanceTableHeader} stockData={rebalanceData} />
          <h3> Capital Incurred: {round_off(capitalIncurred)} INR</h3>
        </div> : <div> Loading... </div>
      }
    </div>
  );
};

