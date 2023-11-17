// import "./App.css";
import React from 'react';

import { StockTable } from './StockTable';
import { DatePickerComponent, StockDatePicker } from './StockDatePicker';


import { nifty200TableHeader, rebalanceTableHeader } from './StockTableHeader';
import { round_off } from './Utils';
import { IRebalanceData, IStockData, IToFromData } from "./StockDataTypes";
import { Accordion, AccordionDetails, AccordionSummary, AppBar, Box, Button, CircularProgress, Container, Drawer, Grid, IconButton, Paper, TextField, Toolbar, Typography, makeStyles } from "@material-ui/core";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import { green, red } from "@material-ui/core/colors";
import MenuIcon from '@material-ui/icons/Menu';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import { SidePanel } from './SidePanel';


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
        const pastStocksData = data[0] as IStockData[];
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
              stock: stock.stock
            } as IToFromData;
          }
          return { symbol: stock.symbol, price: -1, avg_price: stock.price } as IToFromData;
        });

        // Set states
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

  return { rebalanceData, capitalIncurred, currentPrices, loading };
};

interface IViewProps {
  rebalanceData: IRebalanceData[];
  capitalIncurred: number;
  currentPrices: IToFromData[];
  loading: boolean;
}



const useStyles = makeStyles((theme) => ({
  title: {
    color: theme.palette.primary.main,
    marginBottom: theme.spacing(2),
  },
  container: {
    marginTop: theme.spacing(8),
  },
  menuButton: {
    marginLeft: (props: { drawerOpen: boolean }) => props.drawerOpen ? theme.spacing(80) : 0,
  },
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
  },
}));

const ShowTableV2 = (props: IViewProps) => {
  const { rebalanceData, capitalIncurred, currentPrices, loading } = props;
  const fromInvestment = currentPrices.reduce((acc, stock) => acc + stock.investment, 0);
  const toInvestment = currentPrices.reduce((acc, stock) => acc + stock.price * stock.shares, 0);
  const gains = toInvestment - fromInvestment;
  return !loading ? (
    <>
      <Box display="flex" justifyContent="space-between" alignItems="center" padding="1em" bgcolor="#f5f5f5">
        <Typography variant="h6">
          Investment Value: {round_off(fromInvestment)}
        </Typography>
        <Typography variant="h6" style={{
          color: gains > 0 ? green[500] : red[500],
          fontWeight: 'bold',
        }}>
          Current Portfolio Value: {round_off(toInvestment)}
        </Typography>
      </Box>

      <StockTable headers={nifty200TableHeader} stockData={props.currentPrices} />

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
              {capitalIncurred < 0 ? 'Receive' : 'Invest More:'} {Math.abs(round_off(capitalIncurred))}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <StockTable headers={rebalanceTableHeader} stockData={rebalanceData} />
          </AccordionDetails>
        </Accordion>
      </Box>
    </>
  ) : <CircularProgress />;
}

export const App = () => {
  const [fromDateString, setFromDateString] = React.useState<string>('');
  const [toDateString, setToDateString] = React.useState<string>('');
  const [numStocks, setNumStocks] = React.useState<number>(15);
  const [investmentValue, setInvestmentValue] = React.useState<number>(500000);
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const classes = useStyles({ drawerOpen });

  const handleSignOut = () => {
    fetch('/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }).then(() => { logout(); navigate('/login') });
  };

  const { rebalanceData, capitalIncurred, currentPrices, loading }
    = useData(toDateString, fromDateString, numStocks, investmentValue);

  return (
    <div>
      <AppBar position="fixed" className={classes.appBar}>
        <Toolbar>
          <IconButton edge="start" color="inherit" aria-label="menu" onClick={() => setDrawerOpen(!drawerOpen)}>
            <MenuIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <SidePanel
        drawerOpen={drawerOpen}
        numStocks={numStocks}
        setNumStocks={setNumStocks}
        investmentValue={investmentValue}
        setInvestmentValue={setInvestmentValue}
        handleSignOut={handleSignOut}
      />
      <Container maxWidth="xl" className={classes.container}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Typography variant="h4" align="center" gutterBottom className={classes.title}>
              Nifty-200 Momentum Strategy Analyzer
            </Typography>
          </Grid>
          <Grid item xs={12}>
            <DatePickerComponent
              fromDateString={fromDateString}
              toDateString={toDateString}
              setFromDateString={setFromDateString}
              setToDateString={setToDateString}
            />
          </Grid>
          <Grid item xs={12}>
            {fromDateString != '' && toDateString != '' && <ShowTableV2
              rebalanceData={rebalanceData}
              capitalIncurred={capitalIncurred}
              currentPrices={currentPrices}
              loading={loading}
            />
            }
          </Grid>
        </Grid>
      </Container>
    </div>);
};

