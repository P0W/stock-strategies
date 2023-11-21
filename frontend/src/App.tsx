// import "./App.css";
import React from 'react';

import { StockTable } from './StockTable';
import { DatePickerComponent, StockDatePicker } from './StockDatePicker';


import { nifty200TableHeader, rebalanceTableHeader } from './StockTableHeader';
import { drawerWidth } from './Utils';
import { IPortfolio, IRebalanceData, IStockData, ITickerTapeLinks, IToFromData } from "./StockDataTypes";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import { SidePanel } from "./SidePanel";
import { AppBar, Box, CircularProgress, Container, Divider, Grid, IconButton, LinearProgress, makeStyles, Paper, Stack, Toolbar, Typography } from "@mui/material";
import { green, red } from "@mui/material/colors";
import { Accordion, AccordionDetails, AccordionSummary } from "@mui/material";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Navbar } from './Navbar';



const useData = (toDateString: string, fromDateString: string, numStocks: number, investmentValue: number) => {
  const [currentPrices, setCurrentPrices] = React.useState<IToFromData[]>([]);
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
    const fromFetch = fetchData(`/portfolio/${fromDateString}/${numStocks}/${investmentValue}`);
    const nifty200Fetch = fetchData(`/nifty200/${toDateString}`);
    const rebalanceFetch = fetchData(`/rebalance/${fromDateString}/${toDateString}/${numStocks}/${investmentValue}`);

    Promise.all([fromFetch, rebalanceFetch, nifty200Fetch])
      .then(data => {
        const portfolioData = data[0] as IPortfolio;
        const pastStocksData = portfolioData.portfolio as IStockData[];
        const tickertape_links = portfolioData.tickertape_links as ITickerTapeLinks;
        const rebalanceStocksData = data[1] as unknown as { [key: string]: any };
        const nifty200 = data[2] as { [key: string]: number };

        // get the prices for the stocks in the fromDateStocks from nifty200
        const currentStockPrice = pastStocksData.map(stock => {
          const thisStock = Object.keys(nifty200)?.find(niftyStock => niftyStock === stock.symbol);
          if (thisStock) {
            return {
              symbol: stock.symbol,
              avg_price: stock.price,
              weight: stock.weight,
              shares: stock.shares,
              investment: stock.investment,
              price: nifty200[thisStock], // Current price
              stock: stock.stock,
              url: tickertape_links[stock.symbol]
            } as IToFromData;
          }
          return { symbol: stock.symbol, price: -1, avg_price: stock.price } as IToFromData;
        });

        // Update the rebalanceData with the stock name and url
        const rebalanceData = rebalanceStocksData["stocks"] as IRebalanceData[];
        rebalanceData.forEach(stock => {
          const thisStock = Object.keys(nifty200)?.find(niftyStock => niftyStock === stock.symbol);
          if (thisStock) {
            stock.stock = pastStocksData.find(stock => stock.symbol === thisStock)?.stock ?? '';
            stock.url = tickertape_links[thisStock];
          }
        });

        // Set states
        setRebalanceData(rebalanceData);
        setCapitalIncurred(rebalanceStocksData["capital_incurred"]);
        setCurrentPrices(currentStockPrice);
        setLoading(false);
      })
      .catch(err => {
        console.log(err);
        setLoading(false);
      });
  }, [fromDateString, toDateString]);

  return { rebalanceData, capitalIncurred, currentPrices, loading };
};

interface IViewProps {
  rebalanceData: IRebalanceData[];
  capitalIncurred: number;
  currentPrices: IToFromData[];
  loading: boolean;
}


const ShowTableV2 = (props: IViewProps) => {
  const { rebalanceData, capitalIncurred, currentPrices, loading } = props;
  const fromInvestment = currentPrices.reduce((acc, stock) => acc + stock.investment, 0);
  const toInvestment = currentPrices.reduce((acc, stock) => acc + stock.price * stock.shares, 0);
  const gains = toInvestment - fromInvestment;
  return !loading ? (
    <>
      <Paper elevation={1} sx={{
        padding: '1em',
        marginBottom: '1em',
        marginTop: '1em',
        backgroundColor: '#f5f5f5',
      }}>

        <Grid container spacing={2}>
          <Grid item xs={4}>
            <Box p={1}>
              <Typography variant="body1">
                Investment Value: ₹{new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2 }).format(fromInvestment)}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box p={1}>
              <Typography variant="body1">
                Current Portfolio Value: ₹{new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2 }).format(toInvestment)}
                <span style={{ color: gains > 0 ? green[500] : red[500], fontWeight: 'bold' }}>
                  ({new Intl.NumberFormat('en-IN', { style: 'percent', minimumFractionDigits: 2 }).format((gains / fromInvestment))})
                </span>
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box p={1}>
              <Typography variant="body1" style={{
                color: gains > 0 ? green[500] : red[500],
                fontWeight: 'bold'
              }}>
                {gains > 0 ? "Profit" : "Loss"} : ₹{new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2 }).format(gains)}
              </Typography>
            </Box>
          </Grid>
        </Grid>

        <StockTable headers={nifty200TableHeader} stockData={props.currentPrices} />
      </Paper>
      <Box mt={4}>
        <Accordion>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="rebalance-content"
            id="rebalance-header"
          >
            <Typography variant="h6" style={{ fontWeight: 'bold' }}>Rebalance Updates</Typography>
            <Typography variant="subtitle1" style={{
              marginLeft: '1em',
              fontWeight: 'bold',
              color: capitalIncurred < 0 ? green[500] : red[500]
            }}>
              {capitalIncurred < 0 ? 'Receive' : 'Invest More:'} ₹{new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2 }).format(Math.abs(capitalIncurred))}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <StockTable headers={rebalanceTableHeader} stockData={rebalanceData} />
          </AccordionDetails>
        </Accordion>
      </Box>
    </>
  ) : <LinearProgress />;
}

export const App = () => {
  const [fromDateString, setFromDateString] = React.useState<string>('');
  const [toDateString, setToDateString] = React.useState<string>('');
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [numStocks, setNumStocks] = React.useState<number>(user?.num_stocks ?? 15);
  const [investmentValue, setInvestmentValue] = React.useState<number>(user?.investment ?? 500000);

  const handleSignOut = () => {
    fetch('/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }).then(() => { logout(); navigate('/login') });
  };

  React.useEffect(() => {
    setNumStocks(user?.num_stocks ?? 15);
    setInvestmentValue(user?.investment ?? 500000);
  }, [user]);

  const { rebalanceData, capitalIncurred, currentPrices, loading }
    = useData(toDateString, fromDateString, numStocks, investmentValue);

  return (
    <Container maxWidth="xl" disableGutters sx={{
      alignContent: 'center',
      marginTop: '4.5em'
    }}>
      <Navbar handleOpen={() => setDrawerOpen(!drawerOpen)} />
      <SidePanel
        drawerOpen={drawerOpen}
        numStocks={numStocks}
        setNumStocks={setNumStocks}
        investmentValue={investmentValue}
        setInvestmentValue={setInvestmentValue}
        handleSignOut={handleSignOut}
      />
      <Stack spacing={1}>
        <Box >
          <Typography variant="h6" align="center" gutterBottom >
            Nifty-200 Momentum Strategy Analyzer
          </Typography>
        </Box>
        <Box >
          <DatePickerComponent
            fromDateString={fromDateString}
            toDateString={toDateString}
            setFromDateString={setFromDateString}
            setToDateString={setToDateString}
          />
        </Box>
        <Divider />
        <Box >
          {fromDateString != '' && toDateString != '' && <ShowTableV2
            rebalanceData={rebalanceData}
            capitalIncurred={capitalIncurred}
            currentPrices={currentPrices}
            loading={loading}
          />
          }
        </Box>
      </Stack>
    </Container>
  );
};

