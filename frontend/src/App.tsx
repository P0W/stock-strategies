import "./App.css";
import React from 'react';

import { StockTable } from './StockTable';
import { StockDatePicker } from './StockDatePicker';


import { mainTableHeader, nifty200TableHeader, rebalanceTableHeader } from './StockTableHeader';
import { round_off } from './Utils';
import { INifty200Data, IRebalanceData, IStockData, IToFromData } from "./StockDataTypes";
import { Accordion, AccordionDetails, AccordionSummary, Box, Button, CircularProgress, Container, Grid, Paper, TextField, Typography, makeStyles } from "@material-ui/core";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";

const useStyles = makeStyles({
  tableContainer: {
    padding: 10,
    margin: 10,
    height: '65vh',
    overflowY: 'auto',

  },
  portfolioValue: {
    marginBottom: 10,
    fontWeight: 'bold',
    fontSize: '0.75em'
  }
});

const useData = (toDateString: string, fromDateString: string, numStocks: number, investmentValue: number) => {
  const [toDateStocks, setToDateStocks] = React.useState<IStockData[]>([]);
  const [fromDateStocks, setFromDateStocks] = React.useState<IStockData[]>([]);
  const [currentPrices, setCurrentPrices] = React.useState<INifty200Data[]>([]);
  const [rebalanceData, setRebalanceData] = React.useState<IRebalanceData[]>([]);
  const [capitalIncurred, setCapitalIncurred] = React.useState<number>(0);
  const [loading, setLoading] = React.useState(true);
  const cache = React.useRef<{ [key: string]: IStockData[] }>({});

  const fetchData = async (endpoint: string) => {
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
    const rebalanceFetch = fetchData(`/rebalance/${fromDateString}/${toDateString}/${numStocks}/${investmentValue}`);

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
  const navigate = useNavigate();
  const classes = useStyles();
  const { logout } = useAuth();

  const handleSignOut = () => {
    fetch('/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }).then(() => { logout(); navigate('/login') });
  };

  const { toDateStocks, fromDateStocks, rebalanceData, capitalIncurred, currentPrices, loading }
    = useData(toDateString, fromDateString, numStocks, investmentValue);
  // Sum up the investment amount
  const fromInvestment = fromDateStocks.reduce((acc, stock) => acc + stock.investment, 0);
  const toInvestment = toDateStocks.reduce((acc, stock) => acc + stock.investment, 0);
  const currentPortfolioValue = (currentPrices as IToFromData[]).reduce((acc, stock) => acc + stock.shares * stock.price, 0);
  const gains = currentPortfolioValue - fromInvestment;

  return (

    <Container maxWidth="xl">
      <Grid container justifyContent="space-between">
        <Typography variant="h4" align="center" gutterBottom className="title">
          Nifty-200 Momentum Strategy Analyzer
        </Typography>
        <Button variant="contained" color="secondary" onClick={handleSignOut} size="small">
          Sign Out
        </Button>
      </Grid>
      <Grid container spacing={4} justifyContent="center">
        <Grid item>
          <Typography>From:</Typography>
          <StockDatePicker initialDate={fromDateString} onDateChange={setFromDateString} />
        </Grid>
        <Grid item>
          <Typography>To:</Typography>
          <StockDatePicker initialDate={toDateString} onDateChange={setToDateString} startDate={fromDateString} />
        </Grid>
      </Grid>
      <Box my={2}>
        <Accordion>
          <AccordionSummary
            expandIcon={<i className="fas fa-chevron-down"></i>}
            aria-controls="panel1a-content"
            id="panel1a-header"
          >
            <Typography variant="h6">Configurations</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3} alignItems="center">
              <Grid item>
                <Typography>Number of Stocks:</Typography>
                <TextField type="number" value={numStocks} onChange={(e) => setNumStocks(Number(e.target.value))} />
              </Grid>
              <Grid item>
                <Typography>Investment Value:</Typography>
                <TextField type="number" value={investmentValue} onChange={(e) => setInvestmentValue(Number(e.target.value))} />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      </Box>
      {!loading ? (
        <Box my={2}>
          <Paper elevation={3} className="analysis-container">
            <Box p={2} className={classes.tableContainer}>
              <Typography variant="h6" className={classes.portfolioValue}>Investment: {round_off(fromInvestment)} INR | as on {fromDateString}</Typography>
              <StockTable headers={mainTableHeader} stockData={fromDateStocks} />
            </Box>
            <Box p={2} className={classes.tableContainer}>
              <Typography variant="h6" className={classes.portfolioValue} color={gains > 0 ? "primary" : "secondary"}>Gain: {round_off(gains)} INR | as on {toDateString}</Typography>
              <StockTable headers={nifty200TableHeader} stockData={currentPrices} />
            </Box>
            <Box p={2} className={classes.tableContainer}>
              <Typography variant="h6" className={classes.portfolioValue} >New Investment: {round_off(toInvestment)} INR | as on {toDateString}</Typography>
              <StockTable headers={mainTableHeader} stockData={toDateStocks} />
            </Box>
            <Box p={2} className={classes.tableContainer}>
              <Typography variant="h6" className={classes.portfolioValue}>Rebalance Updates | Capital Incurred: {round_off(capitalIncurred)} INR</Typography>
              <StockTable headers={rebalanceTableHeader} stockData={rebalanceData} />
            </Box>
          </Paper>
        </Box>
      ) : (
        fromDateString !== '' && toDateString !== '' && <CircularProgress />
      )}
    </Container>
  );
};

