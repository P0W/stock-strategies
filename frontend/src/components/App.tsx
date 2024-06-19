import React from "react";

import {
  IPortfolio,
  IRebalanceData,
  IStockData,
  ITickerTapeLinks,
  IToFromData,
} from "./StockDataTypes";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { SidePanel } from "./SidePanel";
import {
  Container,
} from "@mui/material";
import { Navbar, Page } from "./Navbar";
import { useInactivityLogout } from "../hooks/useInactivityLogout";
import { StockAnalyzer } from "./StockAnalyzer";
import { StockBalls } from "./StockBalls";
import { StockNews } from "./StockNews";

const useData = (
  toDateString: string,
  fromDateString: string,
  numStocks: number,
  investmentValue: number
) => {
  const [currentPrices, setCurrentPrices] = React.useState<IToFromData[]>([]);
  const [rebalanceData, setRebalanceData] = React.useState<IRebalanceData[]>(
    []
  );
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
    const fromFetch = fetchData(
      `/portfolio/${fromDateString}/${numStocks}/${investmentValue}`
    );
    const nifty200Fetch = fetchData(`/nifty200/${toDateString}`);
    const rebalanceFetch = fetchData(
      `/rebalance/${fromDateString}/${toDateString}/${numStocks}/${investmentValue}`
    );

    Promise.all([fromFetch, rebalanceFetch, nifty200Fetch])
      .then((data) => {
        const portfolioData = data[0] as IPortfolio;
        const pastStocksData = portfolioData.portfolio as IStockData[];
        const tickertape_links =
          portfolioData.tickertape_links as ITickerTapeLinks;
        const rebalanceStocksData = data[1] as unknown as {
          [key: string]: any;
        };
        const nifty200 = data[2] as { [key: string]: number };

        // get the prices for the stocks in the fromDateStocks from nifty200
        const currentStockPrice = pastStocksData.map((stock) => {
          const thisStock = Object.keys(nifty200)?.find(
            (niftyStock) => niftyStock === stock.symbol
          );
          if (thisStock) {
            return {
              symbol: stock.symbol,
              avg_price: stock.price,
              weight: stock.weight,
              shares: stock.shares,
              investment: stock.investment,
              price: nifty200[thisStock], // Current price
              stock: stock.stock,
              url: tickertape_links[stock.symbol],
            } as IToFromData;
          }
          return {
            symbol: stock.symbol,
            price: -1,
            avg_price: stock.price,
          } as IToFromData;
        });

        // Update the rebalanceData with the stock name and url
        const rebalanceData = rebalanceStocksData["stocks"] as IRebalanceData[];
        rebalanceData.forEach((stock) => {
          const thisStock = Object.keys(nifty200)?.find(
            (niftyStock) => niftyStock === stock.symbol
          );
          if (thisStock) {
            stock.stock =
              pastStocksData.find((stock) => stock.symbol === thisStock)
                ?.stock ?? "";
            stock.url = tickertape_links[thisStock];
            stock.initial_shares =
              pastStocksData.find((stock) => stock.symbol === thisStock)
                ?.shares ?? 0;
          }
        });

        // Set states
        setRebalanceData(rebalanceData);
        setCapitalIncurred(rebalanceStocksData["capital_incurred"]);
        setCurrentPrices(currentStockPrice);
        setLoading(false);
      })
      .catch((err) => {
        console.log(err);
        setLoading(false);
      });
  }, [fromDateString, toDateString]);

  return { rebalanceData, capitalIncurred, currentPrices, loading };
};

export const App = () => {
  const [fromDateString, setFromDateString] = React.useState<string>("");
  const [toDateString, setToDateString] = React.useState<string>("");
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [numStocks, setNumStocks] = React.useState<number>(
    user?.num_stocks ?? 15
  );
  const [investmentValue, setInvestmentValue] = React.useState<number>(
    user?.investment ?? 500000
  );
  const [currentPage, setCurrentPage] = React.useState<Page>("Balls");

  const { cleanup, expired } = useInactivityLogout(user);

  const handleSignOut = () => {
    fetch("/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    }).then(() => {
      logout();
      navigate("/login");
      cleanup();
    });
  };

  React.useEffect(() => {
    setNumStocks(user?.num_stocks ?? 15);
    setInvestmentValue(user?.investment ?? 500000);
  }, [user]);

  React.useEffect(() => {
    if (expired) {
      handleSignOut();
    }
  }, [expired]);

  const { rebalanceData, capitalIncurred, currentPrices, loading } = useData(
    toDateString,
    fromDateString,
    numStocks,
    investmentValue
  );

  return (
    <Container
      maxWidth="xl"
      disableGutters
      sx={{
        alignContent: "center",
        marginTop: "4.5em",
      }}
    >
      <Navbar
        handleOpen={() => setDrawerOpen(!drawerOpen)}
        handleLogout={handleSignOut}
        handlePageChange={(page) => setCurrentPage(page)}
      />
      <SidePanel
        drawerOpen={drawerOpen}
        numStocks={numStocks}
        setNumStocks={setNumStocks}
        investmentValue={investmentValue}
        setInvestmentValue={setInvestmentValue}
        handleSignOut={handleSignOut}
      />
      {currentPage === "Analyzer" && (
        <StockAnalyzer
          fromDateString={fromDateString}
          toDateString={toDateString}
          setFromDateString={setFromDateString}
          setToDateString={setToDateString}
          rebalanceData={rebalanceData}
          capitalIncurred={capitalIncurred}
          currentPrices={currentPrices}
          loading={loading}
        />
      )}
      {currentPage === "Balls" && <StockBalls />}
      {currentPage === "Recommendations" && <StockNews />}
    </Container>
  );
};
