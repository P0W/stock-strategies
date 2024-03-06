// StockAnalyzer.tsx
import React from "react";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Divider,
  Grid,
  LinearProgress,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { IRebalanceData, IToFromData } from "./StockDataTypes";
import { green, red } from "@mui/material/colors";
import { StockTable } from "./StockTable";
import { nifty200TableHeader, rebalanceTableHeader } from "./StockTableHeader";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
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
  return !loading ? (
    <>
      <Paper
        elevation={1}
        sx={{
          padding: "1em",
          marginBottom: "1em",
          marginTop: "1em",
          backgroundColor: "#f5f5f5",
        }}
      >
        <Grid container spacing={2}>
          <Grid item xs={4}>
            <Box p={1}>
              <Typography variant="body1">
                Investment Value: ₹
                {new Intl.NumberFormat("en-IN", {
                  minimumFractionDigits: 2,
                }).format(fromInvestment)}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box p={1}>
              <Typography variant="body1">
                Current Portfolio Value: ₹
                {new Intl.NumberFormat("en-IN", {
                  minimumFractionDigits: 2,
                }).format(toInvestment)}
                <span
                  style={{
                    color: gains > 0 ? green[500] : red[500],
                    fontWeight: "bold",
                  }}
                >
                  (
                  {new Intl.NumberFormat("en-IN", {
                    style: "percent",
                    minimumFractionDigits: 2,
                  }).format(gains / fromInvestment)}
                  )
                </span>
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box p={1}>
              <Typography
                variant="body1"
                style={{
                  color: gains > 0 ? green[500] : red[500],
                  fontWeight: "bold",
                }}
              >
                {gains > 0 ? "Profit" : "Loss"} : ₹
                {new Intl.NumberFormat("en-IN", {
                  minimumFractionDigits: 2,
                }).format(gains)}
              </Typography>
            </Box>
          </Grid>
        </Grid>

        <StockTable
          headers={nifty200TableHeader}
          stockData={props.currentPrices}
        />
      </Paper>
      <Box mt={4}>
        <Accordion>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="rebalance-content"
            id="rebalance-header"
          >
            <Typography variant="h6" style={{ fontWeight: "bold" }}>
              Rebalance Updates
            </Typography>
            <Typography
              variant="subtitle1"
              style={{
                marginLeft: "1em",
                fontWeight: "bold",
                color: capitalIncurred < 0 ? green[500] : red[500],
              }}
            >
              {capitalIncurred < 0 ? "Receive" : "Invest More:"} ₹
              {new Intl.NumberFormat("en-IN", {
                minimumFractionDigits: 2,
              }).format(Math.abs(capitalIncurred))}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <StockTable
              headers={rebalanceTableHeader}
              stockData={rebalanceData}
            />
          </AccordionDetails>
        </Accordion>
      </Box>
    </>
  ) : (
    <LinearProgress />
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
    <Stack spacing={1}>
      <Box>
        <Typography variant="h6" align="center" gutterBottom>
          Nifty-200 Momentum Strategy Analyzer
        </Typography>
      </Box>
      <Box>
        <DatePickerComponent
          fromDateString={fromDateString}
          toDateString={toDateString}
          setFromDateString={setFromDateString}
          setToDateString={setToDateString}
        />
      </Box>
      <Divider />
      <Box>
        {fromDateString !== "" && toDateString !== "" && (
          <ShowTableV2
            rebalanceData={rebalanceData}
            capitalIncurred={capitalIncurred}
            currentPrices={currentPrices}
            loading={loading}
          />
        )}
      </Box>
    </Stack>
  );
};
