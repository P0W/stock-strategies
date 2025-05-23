import React from "react";
import { IStockBalls } from "./StockDataTypes";
import {
  Avatar,
  Box,
  Container,
  Grid,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";

export const StockBalls: React.FC = React.memo(() => {
  const [stockBalls, setStockBalls] = React.useState<IStockBalls[]>([]);
  const [searchTerm, setSearchTerm] = React.useState("");

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const todaysDate = new Date().toISOString().split("T")[0];
        const previousDate = new Date();
        previousDate.setDate(previousDate.getDate() - 1);
        const preDateStr = previousDate.toISOString().split("T")[0];
        // try both today's date and yesterday's date
        const res = Promise.all([
          fetch(`/scorecard/${todaysDate}`),
          fetch(`/scorecard/${preDateStr}`),
        ]);
        // use the first successful response
        const data = (await res).find((response) => response.ok);
        setStockBalls(await data?.json());
      } catch (error) {
        console.error("Error fetching stock balls", error);
      }
    };
    fetchData();
  }, []);

  const filteredStockBalls = React.useMemo(() => {
    if (searchTerm && searchTerm.length > 2) {
      return stockBalls?.filter((stockBall) =>
        stockBall.symbol.toLowerCase().includes(searchTerm.toLowerCase())
      );
    } else {
      return stockBalls;
    }
  }, [searchTerm, stockBalls]);

  return (
    <Container maxWidth="lg">
      <Paper
        elevation={1}
        sx={{
          padding: "1em",
          marginBottom: "1em",
          marginTop: "1em",
          backgroundColor: "#f5f5f5",
        }}
      >
        <TextField
          label="Search"
          variant="outlined"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ marginBottom: "1em" }}
        />
        <TableContainer style={{ maxHeight: 800 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell align="center">
                  <Typography variant="h6" component="div">
                    <Box fontWeight="fontWeightBold">S. No.</Box>
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="h6" component="div">
                    <Box fontWeight="fontWeightBold">Stock</Box>
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="h6" component="div">
                    <Box fontWeight="fontWeightBold">Score Card</Box>
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="h6" component="div">
                    <Box fontWeight="fontWeightBold">Composite Score</Box>
                  </Typography>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredStockBalls &&
                filteredStockBalls?.map((stockBall, index) => {
                  return (
                    <TableRow key={index}>
                      <TableCell align="center">{index + 1}</TableCell>
                      <TableCell align="center">
                        <Link
                          href={stockBall.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          underline="none"
                        >
                          <Tooltip title={stockBall.stock}>
                            <Typography variant="h6" component="span">
                              {stockBall.symbol}
                            </Typography>
                          </Tooltip>
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Grid container spacing={1}>
                          {Object.keys(stockBall?.score_card)?.map(
                            (key, index) => {
                              const color = stockBall.score_card[key];
                              return (
                                <Grid item xs={2} key={index}>
                                  <Tooltip title={key}>
                                    <Avatar
                                      variant="circular"
                                      style={{
                                        background: `linear-gradient(45deg, ${color} 30%, ${color} 90%)`,
                                        boxShadow:
                                          "0 3px 5px 2px rgba(0, 0, 0, .3)",
                                        border: 0,
                                        borderRadius: "50%",
                                        width: "20px",
                                        height: "20px",
                                        padding: "5px",
                                        color:
                                          color === "yellow"
                                            ? "black"
                                            : "white",
                                      }}
                                    >
                                      {key[0].toUpperCase()}
                                    </Avatar>
                                  </Tooltip>
                                </Grid>
                              );
                            }
                          )}
                        </Grid>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="h6" component="span">
                          {(stockBall.composite_score * 100).toFixed(1)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  );
                })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
  );
});
