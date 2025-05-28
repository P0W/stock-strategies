import React, { useState, useEffect, useMemo, useCallback } from "react";
import { IStockBalls } from "./StockDataTypes";
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

// Create memoized table row component to prevent unnecessary re-renders
const StockRow = React.memo(
  ({ stockBall, index }: { stockBall: IStockBalls; index: number }) => {
    // Highlight rows with high composite scores
    const getRowStyle = () => {
      const score = stockBall.composite_score;
      if (score >= 0.8) return { backgroundColor: "rgba(76, 175, 80, 0.08)" };
      if (score >= 0.6) return { backgroundColor: "rgba(255, 235, 59, 0.08)" };
      return {};
    };

    return (
      <TableRow
        hover
        style={getRowStyle()}
      >
        <TableCell align="center">{index + 1}</TableCell>
        <TableCell align="center">
          <Link
            href={stockBall.link}
            target="_blank"
            rel="noopener noreferrer"
            underline="hover"
            sx={{
              fontWeight: "bold",
              '&:hover': {
                color: 'primary.main',
                transform: 'scale(1.05)',
                transition: 'transform 0.2s'
              }
            }}
          >
            <Tooltip title={`View details for ${stockBall.stock}`}>
              <Typography variant="h6" component="span">
                {stockBall.symbol}
              </Typography>
            </Tooltip>
          </Link>
        </TableCell>
        <TableCell>
          <Grid
            container
            spacing={1}
            wrap="wrap"
            justifyContent="center"
            alignItems="center"
          >
            {Object.keys(stockBall?.score_card)?.map((key, idx) => {
              const color = stockBall.score_card[key];
              return (
                <Grid item xs="auto" key={idx}>
                  <Tooltip
                    title={<Typography variant="body2">{key}</Typography>}
                    arrow
                    placement="top"
                  >
                    <Avatar
                      variant="circular"
                      sx={{
                        background: `linear-gradient(45deg, ${color} 30%, ${color} 90%)`,
                        boxShadow: "0 3px 5px 2px rgba(0, 0, 0, .3)",
                        border: 0,
                        borderRadius: "50%",
                        width: 30,
                        height: 30,
                        minWidth: 30,
                        margin: "0 3px",
                        padding: 0,
                        color: color === "yellow" ? "black" : "white",
                        fontSize: 16,
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                        fontWeight: "bold",
                        transition: "transform 0.2s",
                        "&:hover": {
                          transform: "scale(1.1)",
                        },
                      }}
                    >
                      {key[0].toUpperCase()}
                    </Avatar>
                  </Tooltip>
                </Grid>
              );
            })}
          </Grid>
        </TableCell>
        <TableCell align="center">
          <Chip
            label={`${(stockBall.composite_score * 100).toFixed(1)}`}
            color={
              stockBall.composite_score >= 0.8 ? "success" :
              stockBall.composite_score >= 0.6 ? "warning" :
              "default"
            }
            sx={{
              fontWeight: "bold",
              fontSize: "1rem",
              minWidth: "60px"
            }}
          />
        </TableCell>
      </TableRow>
    );
  }
);

// Sort types
type SortField = "symbol" | "composite_score" | "indicator" | "";
type SortDirection = "asc" | "desc";
type ColorRank = {
  red: number;
  yellow: number;
  green: number;
  "": number;
  [key: string]: number; // Add index signature to allow string indexing
};

export const StockBalls: React.FC = React.memo(() => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [stockBalls, setStockBalls] = useState<IStockBalls[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [sortField, setSortField] = useState<SortField>("");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [selectedIndicator, setSelectedIndicator] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add debounce effect for search term
  useEffect(() => {
    setIsSearching(true);
    const timerId = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
      setIsSearching(false);
    }, 300); // 300ms delay

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

        // try both today's date and yesterday's date
        const res = Promise.all([
          fetch(`/scorecard/${todaysDate}`),
          fetch(`/scorecard/${preDateStr}`),
        ]);

        // use the first successful response
        const responses = await res;
        const data = responses.find((response) => response.ok);

        if (!data) {
          throw new Error("Unable to fetch scorecard data");
        }

        const result = await data.json();
        setStockBalls(result);
      } catch (error) {
        console.error("Error fetching stock balls", error);
        setError("Failed to load stock data. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Pre-compute lowercase symbols for faster filtering
  const stockBallsWithLowerSymbols = useMemo(() => {
    return stockBalls?.map((ball) => ({
      ...ball,
      lowerSymbol: ball.symbol.toLowerCase(),
    }));
  }, [stockBalls]);

  // Optimize filtering with memoization and debounced search
  const filteredStockBalls = useMemo(() => {
    if (!debouncedSearchTerm || debouncedSearchTerm.length <= 2) {
      return stockBallsWithLowerSymbols;
    }

    const searchLower = debouncedSearchTerm.toLowerCase();
    return stockBallsWithLowerSymbols?.filter((stockBall) =>
      stockBall.lowerSymbol.includes(searchLower)
    );
  }, [debouncedSearchTerm, stockBallsWithLowerSymbols]);

  // Handle search input change with useCallback for performance
  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchTerm(e.target.value);
    },
    []
  );

  // Get unique indicators from all stock balls
  const availableIndicators = useMemo(() => {
    if (!stockBalls || stockBalls.length === 0) return [];

    // Collect all unique indicator keys
    const indicatorSet = new Set<string>();
    stockBalls.forEach((ball) => {
      if (ball.score_card) {
        Object.keys(ball.score_card).forEach((key) => indicatorSet.add(key));
      }
    });

    return Array.from(indicatorSet).sort();
  }, [stockBalls]);

  // Handle sort change
  const handleSortFieldChange = useCallback((event: SelectChangeEvent) => {
    const value = event.target.value as SortField;
    setSortField(value);

    // Reset selected indicator if not sorting by indicator
    if (value !== "indicator") {
      setSelectedIndicator("");
    }
  }, []);

  // Handle indicator change
  const handleIndicatorChange = useCallback((event: SelectChangeEvent) => {
    setSelectedIndicator(event.target.value);
  }, []);

  // Toggle sort direction
  const toggleSortDirection = useCallback(() => {
    setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
  }, []);

  // Sort the data based on sort field and direction
  const sortedStockBalls = useMemo(() => {
    if (!filteredStockBalls || sortField === "") {
      return filteredStockBalls;
    }

    return [...filteredStockBalls].sort((a, b) => {
      let comparison = 0;
      if (sortField === "symbol") {
        comparison = a.symbol.localeCompare(b.symbol);
      } else if (sortField === "composite_score") {
        comparison = a.composite_score - b.composite_score;
      } else if (sortField === "indicator" && selectedIndicator) {
        // Sort by specific ball indicator
        const colorA = a.score_card[selectedIndicator] || "";
        const colorB = b.score_card[selectedIndicator] || "";

        // Define a color ranking for sorting (red is worst, green is best)
        const colorRank: ColorRank = { red: 0, yellow: 1, green: 2, "": -1 };
        comparison = (colorRank[colorA] ?? -1) - (colorRank[colorB] ?? -1);
      }

      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [filteredStockBalls, sortField, sortDirection, selectedIndicator]);

  // Chunk the data to improve rendering performance
  const chunkedStockBalls = useMemo(() => {
    if (!sortedStockBalls) return [];

    // Only show first 50 items initially if searching
    if (debouncedSearchTerm && sortedStockBalls.length > 50) {
      return sortedStockBalls.slice(0, 50);
    }

    // Otherwise, show everything
    return sortedStockBalls;
  }, [sortedStockBalls, debouncedSearchTerm]);

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Card
        elevation={3}
        sx={{
          borderRadius: 2,
          overflow: 'hidden',
          mb: 4
        }}
      >
        <Box
          sx={{
            p: 2,
            background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
            color: 'white',
          }}
        >
          <Typography variant="h4" component="h1" gutterBottom>
            Stock Scorecard
          </Typography>
          <Typography variant="subtitle1">
            Analyze stock performance with our comprehensive scorecard system
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
                placeholder="Enter stock symbol to search..."
                fullWidth
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  style: { borderRadius: 8 },
                }}
              />
              {debouncedSearchTerm && filteredStockBalls && (
                <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary' }}>
                  Found {filteredStockBalls.length} matches for "{debouncedSearchTerm}"
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
                    <MenuItem value="symbol">Stock Symbol</MenuItem>
                    <MenuItem value="composite_score">Composite Score</MenuItem>
                    <MenuItem value="indicator">Indicator Ball</MenuItem>
                  </Select>
                </FormControl>

                {sortField === "indicator" && (
                  <FormControl variant="outlined" fullWidth>
                    <InputLabel id="indicator-label">Select Indicator</InputLabel>
                    <Select
                      labelId="indicator-label"
                      value={selectedIndicator}
                      onChange={handleIndicatorChange}
                      label="Select Indicator"
                      sx={{ borderRadius: 2 }}
                    >
                      {availableIndicators.map((indicator) => (
                        <MenuItem key={indicator} value={indicator}>
                          {indicator}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}

                {sortField && (
                  <IconButton
                    onClick={toggleSortDirection}
                    color="primary"
                    aria-label={`Sort ${
                      sortDirection === "asc" ? "ascending" : "descending"
                    }`}
                    sx={{
                      bgcolor: 'rgba(33, 150, 243, 0.1)',
                      '&:hover': {
                        bgcolor: 'rgba(33, 150, 243, 0.2)',
                      }
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

          <Box sx={{ position: 'relative', minHeight: '200px' }}>
            {isLoading ? (
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '400px'
                }}
              >
                <CircularProgress />
                <Typography variant="h6" sx={{ ml: 2 }}>
                  Loading stock data...
                </Typography>
              </Box>
            ) : error ? (
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '200px'
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
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          S. No.
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          Stock
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Box display="flex" alignItems="center" justifyContent="center">
                          <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                            Score Card
                          </Typography>
                          <Tooltip title="Color indicators represent different metrics: Green (good), Yellow (neutral), Red (caution)">
                            <IconButton size="small">
                              <InfoOutlinedIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          Composite Score
                        </Typography>
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {!isSearching &&
                      chunkedStockBalls?.map((stockBall, index) => (
                        <StockRow
                          key={stockBall.symbol || index}
                          stockBall={stockBall}
                          index={index}
                        />
                      ))}
                  </TableBody>
                </Table>

                {!isSearching && chunkedStockBalls?.length === 0 && (
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      height: '200px'
                    }}
                  >
                    <Typography variant="h6" color="text.secondary">
                      No stocks found matching your criteria
                    </Typography>
                  </Box>
                )}
              </TableContainer>
            )}
          </Box>

          {chunkedStockBalls && filteredStockBalls &&
           chunkedStockBalls.length < filteredStockBalls.length && (
            <Box mt={2} textAlign="center">
              <Typography variant="body2" color="text.secondary">
                Showing {chunkedStockBalls.length} of {filteredStockBalls.length} stocks
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Container>
  );
});
