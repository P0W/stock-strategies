import React from "react";
import { IStockNews } from "./StockDataTypes";
import {
  Container,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { blue, grey, green, red, yellow } from "@mui/material/colors";

export const StockNews: React.FC = React.memo(() => {
  const [stockNews, setStockNews] = React.useState<IStockNews[]>([]);
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
          fetch(`/stocknews/${todaysDate}`),
          fetch(`/stocknews/${preDateStr}`),
        ]);
        // use the first successful response
        const data = (await res).find((response) => response.ok);
        setStockNews(await data?.json());
      } catch (error) {
        console.error("Error fetching stock news", error);
      }
    };
    fetchData();
  }, []);

  const filteredStockNews = React.useMemo(() => {
    if (searchTerm && searchTerm.length > 2) {
      return stockNews?.filter((news) =>
        news.stock.toLowerCase().includes(searchTerm.toLowerCase())
      );
    } else {
      return stockNews;
    }
  }, [searchTerm, stockNews]);

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case "BUY":
      case "Buy": // Add "Buy" as a valid recommendation
        return green[500]; // Use green for BUY
      case "SELL":
      case "Sell": // Add "Sell" as a valid recommendation
        return red[500]; // Use red for SELL
      case "HOLD":
      case "Hold": // Add "Hold" as a valid recommendation
        return yellow[700]; // Use yellow for HOLD
      case "ACCUMULATE":
      case "Accumulate": // Add "Accumulate" as a valid recommendation
        return blue[500]; // Use blue for ACCUMULATE
      default:
        return "inherit"; // Use default color
    }
  };

  return (
    <Container maxWidth="lg">
      <Paper elevation={1} style={{ padding: "1rem", marginBottom: "1rem" }}>
        <Typography variant="h4">Stock News</Typography>
        <TextField
          label="Search"
          variant="outlined"
          fullWidth
          margin="normal"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell
                  style={{
                    fontWeight: "bold",
                    color: "#1976d2",
                    fontSize: "1rem",
                    textAlign: "left",
                  }}
                >
                  S. No.
                </TableCell>
                <TableCell
                  style={{
                    fontWeight: "bold",
                    color: "#1976d2",
                    fontSize: "1rem",
                    textAlign: "left",
                  }}
                >
                  Stock
                </TableCell>
                <TableCell
                  style={{
                    fontWeight: "bold",
                    color: "#1976d2",
                    fontSize: "1rem",
                    textAlign: "left",
                  }}
                >
                  Recommendation
                </TableCell>
                <TableCell
                  style={{
                    fontWeight: "bold",
                    color: "#1976d2",
                    fontSize: "1rem",
                    textAlign: "left",
                  }}
                >
                  Broker
                </TableCell>
                <TableCell
                  style={{
                    fontWeight: "bold",
                    color: "#1976d2",
                    fontSize: "1rem",
                    textAlign: "left",
                  }}
                >
                  Target Price
                </TableCell>
                <TableCell
                  style={{
                    fontWeight: "bold",
                    color: "#1976d2",
                    fontSize: "1rem",
                    textAlign: "left",
                  }}
                >
                  Date
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredStockNews?.map((news, index) => (
                <TableRow key={news.stock}>
                  <TableCell style={{ textAlign: "left", padding: "8px" }}>
                    {index + 1}
                  </TableCell>
                  <TableCell style={{ textAlign: "left", padding: "8px" }}>
                    <Link
                      href={news.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        fontWeight: "bold",
                        textDecoration: "none",
                        color: "#1976d2",
                      }}
                    >
                      {news.stock}
                    </Link>
                  </TableCell>
                  <TableCell
                    style={{
                      textAlign: "left",
                      padding: "8px",
                      color: getRecommendationColor(news.recommendation),
                    }}
                  >
                    <b style={{ textTransform: "uppercase" }}>
                      {news.recommendation}
                    </b>
                  </TableCell>
                  <TableCell style={{ textAlign: "left", padding: "8px" }}>
                    {news.broker}
                  </TableCell>
                  <TableCell style={{ textAlign: "left", padding: "8px" }}>
                    ₹{news.target_price.toFixed(2)}
                  </TableCell>
                  <TableCell style={{ textAlign: "left", padding: "8px" }}>
                    {new Date(news.published_date).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
  );
});
