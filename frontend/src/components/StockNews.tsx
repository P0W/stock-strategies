import React, { useState, useEffect, useMemo, useCallback } from "react";
import { IStockNews } from "./StockDataTypes";
import {
  Avatar,
  Box,
  CircularProgress,
  Container,
  Divider,
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
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Stack,
  useTheme,
  useMediaQuery,
  Chip,
  Card,
  CardContent,
} from "@mui/material";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import SearchIcon from "@mui/icons-material/Search";
import SortIcon from "@mui/icons-material/Sort";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { blue, grey, green, red, yellow } from "@mui/material/colors";

// Create memoized table row component
const NewsRow = React.memo(
  ({ news, index }: { news: IStockNews; index: number }) => {
    const getRecommendationColor = (recommendation: string) => {
      switch (recommendation) {
        case "BUY":
        case "Buy":
          return "success";
        case "SELL":
        case "Sell":
          return "error";
        case "HOLD":
        case "Hold":
          return "warning";
        case "ACCUMULATE":
        case "Accumulate":
          return "info";
        default:
          return "default";
      }
    };

    return (
      <TableRow hover>
        <TableCell align="center">{index + 1}</TableCell>
        <TableCell align="center">
          <Link
            href={news.url}
            target="_blank"
            rel="noreferrer"
            underline="hover"
            sx={{
              fontWeight: "bold",
              "&:hover": {
                color: "primary.main",
                transform: "scale(1.05)",
                transition: "transform 0.2s",
              },
            }}
          >
            <Typography variant="h6" component="span">
              {news.stock}
            </Typography>
          </Link>
        </TableCell>
        <TableCell align="center">
          <Chip
            label={news.recommendation}
            color={getRecommendationColor(news.recommendation)}
            sx={{
              fontWeight: "bold",
              textTransform: "uppercase",
            }}
          />
        </TableCell>
        <TableCell align="center">
          <Typography variant="body1">{news.broker}</Typography>
        </TableCell>
        <TableCell align="center">
          <Typography variant="h6" component="span" sx={{ fontWeight: "bold" }}>
            ₹{news.target_price.toFixed(2)}
          </Typography>
        </TableCell>
        <TableCell align="center">
          <Typography variant="body2">
            {new Date(news.published_date).toLocaleDateString()}
          </Typography>
        </TableCell>
      </TableRow>
    );
  }
);

// Sort types
type SortField =
  | "stock"
  | "recommendation"
  | "broker"
  | "target_price"
  | "published_date"
  | "";
type SortDirection = "asc" | "desc";

export const StockNews: React.FC = React.memo(() => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [stockNews, setStockNews] = useState<IStockNews[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [sortField, setSortField] = useState<SortField>("");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add debounce effect for search term
  useEffect(() => {
    setIsSearching(true);
    const timerId = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
      setIsSearching(false);
    }, 300);

    return () => {
      clearTimeout(timerId);
    };
  }, [searchTerm]);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const todaysDate = new Date().toISOString().split("T")[0];
        const previousDate = new Date();
        previousDate.setDate(previousDate.getDate() - 1);
        const preDateStr = previousDate.toISOString().split("T")[0];

        const res = Promise.all([
          fetch(`/stocknews/${todaysDate}`),
          fetch(`/stocknews/${preDateStr}`),
        ]);

        const responses = await res;
        const data = responses.find((response) => response.ok);

        if (!data) {
          throw new Error("Unable to fetch stock news data");
        }

        let stockNews: IStockNews[] = await data.json();
        stockNews.sort((a, b) => {
          if (a.stock < b.stock) {
            return -1;
          } else if (a.stock > b.stock) {
            return 1;
          } else {
            return (
              new Date(b.published_date).getTime() -
              new Date(a.published_date).getTime()
            );
          }
        });
        setStockNews(stockNews);
      } catch (error) {
        console.error("Error fetching stock news", error);
        setError("Failed to load stock news. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  // Pre-compute lowercase stocks for faster filtering
  const stockNewsWithLowerStocks = useMemo(() => {
    return stockNews?.map((news) => ({
      ...news,
      lowerStock: news.stock.toLowerCase(),
    }));
  }, [stockNews]);

  // Optimize filtering with memoization and debounced search
  const filteredStockNews = useMemo(() => {
    if (!debouncedSearchTerm || debouncedSearchTerm.length <= 2) {
      return stockNewsWithLowerStocks;
    }

    const searchLower = debouncedSearchTerm.toLowerCase();
    return stockNewsWithLowerStocks?.filter((news) =>
      news.lowerStock.includes(searchLower)
    );
  }, [debouncedSearchTerm, stockNewsWithLowerStocks]);

  // Handle search input change
  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchTerm(e.target.value);
    },
    []
  );

  // Handle sort change
  const handleSortFieldChange = useCallback((event: SelectChangeEvent) => {
    setSortField(event.target.value as SortField);
  }, []);

  // Toggle sort direction
  const toggleSortDirection = useCallback(() => {
    setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
  }, []);

  // Sort the data based on sort field and direction
  const sortedStockNews = useMemo(() => {
    if (!filteredStockNews || sortField === "") {
      return filteredStockNews;
    }

    return [...filteredStockNews].sort((a, b) => {
      let comparison = 0;
      if (sortField === "stock") {
        comparison = a.stock.localeCompare(b.stock);
      } else if (sortField === "recommendation") {
        comparison = a.recommendation.localeCompare(b.recommendation);
      } else if (sortField === "broker") {
        comparison = a.broker.localeCompare(b.broker);
      } else if (sortField === "target_price") {
        comparison = a.target_price - b.target_price;
      } else if (sortField === "published_date") {
        comparison =
          new Date(a.published_date).getTime() -
          new Date(b.published_date).getTime();
      }

      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [filteredStockNews, sortField, sortDirection]);

  // Chunk the data to improve rendering performance
  const chunkedStockNews = useMemo(() => {
    if (!sortedStockNews) return [];

    if (debouncedSearchTerm && sortedStockNews.length > 50) {
      return sortedStockNews.slice(0, 50);
    }

    return sortedStockNews;
  }, [sortedStockNews, debouncedSearchTerm]);

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Card
        elevation={3}
        sx={{
          borderRadius: 2,
          overflow: "hidden",
          mb: 4,
        }}
      >
        <Box
          sx={{
            p: 2,
            background:
              "linear-gradient(45deg, #FF6B6B 30%, #FF8E53 90%)",
            color: "white",
          }}
        >
          <Typography variant="h4" component="h1" gutterBottom>
            Stock News & Recommendations
          </Typography>
          <Typography variant="subtitle1">
            Latest stock recommendations and analysis from top brokers
          </Typography>
        </Box>
        <CardContent>
          <Grid container spacing={3} alignItems="center" mb={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Search Stocks"
                variant="outlined"
                value={searchTerm}
                onChange={handleSearchChange}
                placeholder="Enter stock name to search..."
                fullWidth
                InputProps={{
                  startAdornment: (
                    <SearchIcon
                      sx={{ mr: 1, color: "text.secondary" }}
                      fontSize="small"
                    />
                  ),
                  style: { borderRadius: 8 },
                }}
              />
              {debouncedSearchTerm && filteredStockNews && (
                <Typography
                  variant="body2"
                  sx={{ mt: 1, color: "text.secondary" }}
                >
                  Found {filteredStockNews.length} matches for "
                  {debouncedSearchTerm}"
                </Typography>
              )}
            </Grid>
            <Grid item xs={12} md={6}>
              <Stack
                direction={isMobile ? "column" : "row"}
                spacing={2}
                alignItems="center"
              >
                <FormControl variant="outlined" fullWidth>
                  <InputLabel id="sort-by-label">
                    <Box display="flex" alignItems="center">
                      <SortIcon sx={{ mr: 0.5 }} fontSize="small" />
                      Sort By
                    </Box>
                  </InputLabel>
                  <Select
                    labelId="sort-by-label"
                    value={sortField}
                    onChange={handleSortFieldChange}
                    label="Sort By"
                    sx={{ borderRadius: 2 }}
                  >
                    <MenuItem value="">
                      <em>None</em>
                    </MenuItem>
                    <MenuItem value="stock">Stock Name</MenuItem>
                    <MenuItem value="recommendation">Recommendation</MenuItem>
                    <MenuItem value="broker">Broker</MenuItem>
                    <MenuItem value="target_price">Target Price</MenuItem>
                    <MenuItem value="published_date">Date</MenuItem>
                  </Select>
                </FormControl>

                {sortField && (
                  <IconButton
                    onClick={toggleSortDirection}
                    color="primary"
                    aria-label={`Sort ${
                      sortDirection === "asc" ? "ascending" : "descending"
                    }`}
                    sx={{
                      bgcolor: "rgba(255, 107, 107, 0.1)",
                      "&:hover": {
                        bgcolor: "rgba(255, 107, 107, 0.2)",
                      },
                    }}
                  >
                    {sortDirection === "asc" ? (
                      <ArrowUpwardIcon />
                    ) : (
                      <ArrowDownwardIcon />
                    )}
                  </IconButton>
                )}
              </Stack>
            </Grid>
          </Grid>

          <Box mb={2}>
            <Divider />
          </Box>

          <Box sx={{ position: "relative", minHeight: "200px" }}>
            {isLoading ? (
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  height: "400px",
                }}
              >
                <CircularProgress />
                <Typography variant="h6" sx={{ ml: 2 }}>
                  Loading stock news...
                </Typography>
              </Box>
            ) : error ? (
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  height: "200px",
                }}
              >
                <Typography color="error" variant="h6">
                  {error}
                </Typography>
              </Box>
            ) : (
              <TableContainer sx={{ maxHeight: 600, borderRadius: 1 }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell align="center">
                        <Typography
                          variant="subtitle1"
                          sx={{ fontWeight: "bold" }}
                        >
                          S. No.
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography
                          variant="subtitle1"
                          sx={{ fontWeight: "bold" }}
                        >
                          Stock
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography
                          variant="subtitle1"
                          sx={{ fontWeight: "bold" }}
                        >
                          Recommendation
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography
                          variant="subtitle1"
                          sx={{ fontWeight: "bold" }}
                        >
                          Broker
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography
                          variant="subtitle1"
                          sx={{ fontWeight: "bold" }}
                        >
                          Target Price
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography
                          variant="subtitle1"
                          sx={{ fontWeight: "bold" }}
                        >
                          Date
                        </Typography>
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {!isSearching &&
                      chunkedStockNews?.map((news, index) => (
                        <NewsRow
                          key={`${news.stock}-${news.broker}-${index}`}
                          news={news}
                          index={index}
                        />
                      ))}
                  </TableBody>
                </Table>

                {!isSearching && chunkedStockNews?.length === 0 && (
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      height: "200px",
                    }}
                  >
                    <Typography variant="h6" color="text.secondary">
                      No stock news found matching your criteria
                    </Typography>
                  </Box>
                )}
              </TableContainer>
            )}
          </Box>

          {chunkedStockNews &&
            filteredStockNews &&
            chunkedStockNews.length < filteredStockNews.length && (
              <Box mt={2} textAlign="center">
                <Typography variant="body2" color="text.secondary">
                  Showing {chunkedStockNews.length} of{" "}
                  {filteredStockNews.length} news items
                </Typography>
              </Box>
            )}
        </CardContent>
      </Card>
    </Container>
  );
});
