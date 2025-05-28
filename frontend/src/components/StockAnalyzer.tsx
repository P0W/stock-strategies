// StockAnalyzer.tsx
import React from "react";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Card,
  CardContent,
  Chip,
  Container,
  Divider,
  Grid,
  LinearProgress,
  Paper,
  Stack,
  Typography,
  Alert,
} from "@mui/material";
import { IRebalanceData, IToFromData } from "./StockDataTypes";
import { green, grey, red, blue } from "@mui/material/colors";
import { StockTable } from "./StockTable";
import { nifty200TableHeader, rebalanceTableHeader } from "./StockTableHeader";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import ShowChartIcon from "@mui/icons-material/ShowChart";
import SwapHorizIcon from "@mui/icons-material/SwapHoriz";
import { DatePickerComponent } from "./StockDatePicker";

interface StockAnalyzerProps {
  fromDateString: string;
  toDateString: string;
  setFromDateString: (date: string) => void;
  setToDateString: (date: string) => void;
  rebalanceData: any; // replace with the actual type
  capitalIncurred: any; // replace with the actual type
  currentPrices: any; // replace with the actual type
  loading: boolean;
}

interface IViewProps {
  rebalanceData: IRebalanceData[];
  capitalIncurred: number;
  currentPrices: IToFromData[];
  loading: boolean;
}

const ShowTableV2 = (props: IViewProps) => {
  const { rebalanceData, capitalIncurred, currentPrices, loading } = props;
  const fromInvestment = currentPrices.reduce(
    (acc, stock) => acc + stock.investment,
    0
  );
  const toInvestment = currentPrices.reduce(
    (acc, stock) => acc + stock.price * stock.shares,
    0
  );
  const gains = toInvestment - fromInvestment;
  // Count number of stock selling, buying and holding
  const sell = rebalanceData.filter(
    (stock: IRebalanceData) => stock.shares < 0
  ).length;
  const buy = rebalanceData.filter(
    (stock: IRebalanceData) => stock.shares > 0
  ).length;
  const hold = rebalanceData.filter(
    (stock: IRebalanceData) => stock.shares === 0
  ).length;

  if (loading) {
    return (
      <Box sx={{ mt: 4 }}>
        <Paper sx={{ p: 3, textAlign: "center" }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Analyzing your portfolio...
          </Typography>
          <LinearProgress sx={{ mt: 2 }} />
        </Paper>
      </Box>
    );
  }

  return (
    <>
      {/* Portfolio Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card
            elevation={3}
            sx={{
              height: "100%",
              background:
                "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            }}
          >
            <CardContent sx={{ color: "white", textAlign: "center" }}>
              <AccountBalanceWalletIcon sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6" gutterBottom>
                Initial Investment
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                ₹
                {new Intl.NumberFormat("en-IN", { minimumFractionDigits: 0 }).format(
                  fromInvestment
                )}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            elevation={3}
            sx={{
              height: "100%",
              background:
                "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            }}
          >
            <CardContent sx={{ color: "white", textAlign: "center" }}>
              <ShowChartIcon sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6" gutterBottom>
                Current Value
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                ₹
                {new Intl.NumberFormat("en-IN", { minimumFractionDigits: 0 }).format(
                  toInvestment
                )}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            elevation={3}
            sx={{
              height: "100%",
              background:
                gains >= 0
                  ? "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
                  : "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
            }}
          >
            <CardContent sx={{ color: "white", textAlign: "center" }}>
              {gains >= 0 ? (
                <TrendingUpIcon sx={{ fontSize: 40, mb: 1 }} />
              ) : (
                <TrendingDownIcon sx={{ fontSize: 40, mb: 1 }} />
              )}
              <Typography variant="h6" gutterBottom>
                {gains >= 0 ? "Total Profit" : "Total Loss"}
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                ₹
                {new Intl.NumberFormat("en-IN", { minimumFractionDigits: 0 }).format(
                  Math.abs(gains)
                )}
              </Typography>
              <Chip
                label={`${new Intl.NumberFormat("en-IN", {
                  style: "percent",
                  minimumFractionDigits: 2,
                }).format(gains / fromInvestment)}`}
                sx={{
                  mt: 1,
                  backgroundColor: "rgba(255,255,255,0.2)",
                  color: "white",
                  fontWeight: "bold",
                }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Current Holdings Table */}
      <Paper elevation={2} sx={{ mb: 4 }}>
        <Box
          sx={{
            p: 3,
            borderBottom: "1px solid",
            borderColor: "divider",
          }}
        >
          <Typography variant="h5" fontWeight="bold" color="primary">
            📊 Current Portfolio Holdings
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Detailed view of your current stock positions
          </Typography>
        </Box>
        <Box sx={{ p: 2 }}>
          <StockTable headers={nifty200TableHeader} stockData={currentPrices} />
        </Box>
      </Paper>

      {/* Rebalance Section */}
      <Accordion elevation={3} sx={{ mb: 2 }}>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          sx={{
            backgroundColor: "#f8f9fa",
            "&:hover": { backgroundColor: "#e9ecef" },
            borderRadius: "8px 8px 0 0",
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 2,
              width: "100%",
            }}
          >
            <SwapHorizIcon color="primary" />
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h6" fontWeight="bold">
                🔄 Portfolio Rebalancing
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Click to view recommended buy/sell actions
              </Typography>
            </Box>
            <Chip
              label={`${capitalIncurred < 0 ? "Receive" : "Invest"} ₹${new Intl.NumberFormat(
                "en-IN",
                {
                  minimumFractionDigits: 0,
                }
              ).format(Math.abs(capitalIncurred))}`}
              color={capitalIncurred < 0 ? "success" : "warning"}
              variant="filled"
              sx={{ fontWeight: "bold" }}
            />
          </Box>
        </AccordionSummary>
        <AccordionDetails sx={{ p: 0 }}>
          <Box sx={{ p: 3 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Rebalancing Summary:</strong> This shows the actions needed
                to optimize your portfolio allocation.
              </Typography>
            </Alert>

            <StockTable headers={rebalanceTableHeader} stockData={rebalanceData} />

            <Box
              sx={{
                mt: 3,
                p: 2,
                backgroundColor: "#f8f9fa",
                borderRadius: 2,
              }}
            >
              <Typography variant="h6" gutterBottom fontWeight="bold">
                📈 Action Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Box textAlign="center">
                    <Chip
                      label={`${buy} Stocks`}
                      color="success"
                      variant="outlined"
                      sx={{ mb: 1, fontWeight: "bold" }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      Buy More
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={4}>
                  <Box textAlign="center">
                    <Chip
                      label={`${sell} Stocks`}
                      color="error"
                      variant="outlined"
                      sx={{ mb: 1, fontWeight: "bold" }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      Sell Positions
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={4}>
                  <Box textAlign="center">
                    <Chip
                      label={`${hold} Stocks`}
                      color="default"
                      variant="outlined"
                      sx={{ mb: 1, fontWeight: "bold" }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      Hold Current
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>
    </>
  );
};

export const StockAnalyzer: React.FC<StockAnalyzerProps> = ({
  fromDateString,
  toDateString,
  setFromDateString,
  setToDateString,
  rebalanceData,
  capitalIncurred,
  currentPrices,
  loading,
}) => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack spacing={4}>
        {/* Header Section */}
        <Paper
          elevation={3}
          sx={{
            p: 4,
            textAlign: "center",
            background:
              "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color: "white",
          }}
        >
          <Typography variant="h3" fontWeight="bold" gutterBottom>
            📈 Nifty-200 Momentum Strategy
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.9 }}>
            Analyze and optimize your portfolio performance with data-driven insights
          </Typography>
        </Paper>

        {/* Date Picker Section */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography
            variant="h5"
            fontWeight="bold"
            gutterBottom
            color="primary"
          >
            📅 Select Analysis Period
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Choose your investment timeframe to analyze portfolio performance
          </Typography>
          <DatePickerComponent
            fromDateString={fromDateString}
            toDateString={toDateString}
            setFromDateString={setFromDateString}
            setToDateString={setToDateString}
          />
        </Paper>

        {/* Results Section */}
        {fromDateString !== "" && toDateString !== "" ? (
          <ShowTableV2
            rebalanceData={rebalanceData}
            capitalIncurred={capitalIncurred}
            currentPrices={currentPrices}
            loading={loading}
          />
        ) : (
          <Alert severity="info" sx={{ textAlign: "center" }}>
            <Typography variant="h6">
              👆 Please select both start and end dates to begin your portfolio
              analysis
            </Typography>
          </Alert>
        )}
      </Stack>
    </Container>
  );
};
