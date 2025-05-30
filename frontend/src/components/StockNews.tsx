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
import { DatePickerComponent } from "./StockDatePicker";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import GroupIcon from "@mui/icons-material/Group";
import StarIcon from "@mui/icons-material/Star";
import InsightsIcon from "@mui/icons-material/Insights";
import TrendingFlatIcon from "@mui/icons-material/TrendingFlat";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import LightbulbIcon from "@mui/icons-material/Lightbulb";

// Create memoized table row component
const NewsRow = React.memo(
  ({
    news,
    index,
    stockCounts,
    isMultipleBrokers,
  }: {
    news: IStockNews;
    index: number;
    stockCounts: Record<string, number>;
    isMultipleBrokers: boolean;
  }) => {
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

    const brokerCount = stockCounts[news.stock] || 1;

    return (
      <TableRow
        hover
        sx={{
          backgroundColor: isMultipleBrokers
            ? "rgba(255, 193, 7, 0.1)"
            : "inherit",
          borderLeft: isMultipleBrokers ? "4px solid #ffc107" : "none",
          "&:hover": {
            backgroundColor: isMultipleBrokers
              ? "rgba(255, 193, 7, 0.15)"
              : "rgba(0, 0, 0, 0.04)",
          },
        }}
      >
        <TableCell align="center">{index + 1}</TableCell>
        <TableCell align="center">
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 1,
            }}
          >
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
            {isMultipleBrokers && (
              <Tooltip
                title={`${brokerCount} brokers recommend this stock`}
                arrow
              >
                <Chip
                  icon={<GroupIcon />}
                  label={brokerCount}
                  color="warning"
                  size="small"
                  sx={{
                    fontWeight: "bold",
                    fontSize: "0.75rem",
                    height: "24px",
                    "& .MuiChip-icon": {
                      fontSize: "16px",
                    },
                    animation: "pulse 2s infinite",
                    "@keyframes pulse": {
                      "0%": {
                        transform: "scale(1)",
                      },
                      "50%": {
                        transform: "scale(1.05)",
                      },
                      "100%": {
                        transform: "scale(1)",
                      },
                    },
                  }}
                />
              </Tooltip>
            )}
          </Box>
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

  // Add date picker states
  const [selectedDate, setSelectedDate] = useState("");
  const [availableDates, setAvailableDates] = useState<string[]>([]);

  // Add analytics state with caching
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsCache, setAnalyticsCache] = useState<any>(null);
  const [analyticsCacheTimestamp, setAnalyticsCacheTimestamp] = useState<number | null>(null);

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
        // If a specific date is selected, only fetch for that date
        if (selectedDate) {
          const res = await fetch(`/stocknews/${selectedDate}`);
          if (!res.ok) {
            throw new Error(`No data available for ${selectedDate}`);
          }
          let stockNews: IStockNews[] = await res.json();
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
        } else {
          // Default behavior - fetch today and yesterday
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
        }
      } catch (error) {
        console.error("Error fetching stock news", error);
        setError("Failed to load stock news. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [selectedDate]);

  // Fetch available dates on component mount
  useEffect(() => {
    const fetchAvailableDates = async () => {
      try {
        // Generate dates for the last 30 days
        const dates = [];
        const today = new Date();
        for (let i = 0; i < 30; i++) {
          const date = new Date(today);
          date.setDate(today.getDate() - i);
          dates.push(date.toISOString().split("T")[0]);
        }
        setAvailableDates(dates);
      } catch (error) {
        console.warn("Could not fetch available dates");
      }
    };
    fetchAvailableDates();
  }, []);

  // Fetch 15-day analytics when no date is selected with caching
  useEffect(() => {
    const fetchAnalytics = async () => {
      if (selectedDate) return; // Only fetch when no specific date is selected
      
      // Check if we have valid cached data (less than 15 minutes old)
      const cacheValidityDuration = 15 * 60 * 1000; // 15 minutes in milliseconds
      const now = Date.now();
      
      if (analyticsCache && analyticsCacheTimestamp && 
          (now - analyticsCacheTimestamp) < cacheValidityDuration) {
        console.log('Using cached analytics data');
        setAnalyticsData(analyticsCache);
        return;
      }
      
      setAnalyticsLoading(true);
      try {
        console.log('Fetching fresh analytics data...');
        const today = new Date();
        const promises = [];
        
        // Fetch last 15 days of data
        for (let i = 0; i < 15; i++) {
          const date = new Date(today);
          date.setDate(today.getDate() - i);
          const dateStr = date.toISOString().split('T')[0];
          promises.push(
            fetch(`/stocknews/${dateStr}`)
              .then(res => res.ok ? res.json() : [])
              .catch(() => [])
          );
        }

        const allResults = await Promise.all(promises);
        const combinedData = allResults.flat();
        
        // Analyze the data
        const stockCounts: Record<string, number> = {};
        const brokerCounts: Record<string, number> = {};
        const recommendationCounts: Record<string, number> = {};
        
        combinedData.forEach((news: IStockNews) => {
          stockCounts[news.stock] = (stockCounts[news.stock] || 0) + 1;
          brokerCounts[news.broker] = (brokerCounts[news.broker] || 0) + 1;
          recommendationCounts[news.recommendation] = (recommendationCounts[news.recommendation] || 0) + 1;
        });

        const multipleRecommendations = Object.entries(stockCounts)
          .filter(([_, count]) => count >= 3)
          .sort(([, a], [, b]) => b - a);

        const topBrokers = Object.entries(brokerCounts)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 3);

        const topRecommendation = Object.entries(recommendationCounts)
          .sort(([, a], [, b]) => b - a)[0];

        const analyticsResult = {
          totalRecommendations: combinedData.length,
          uniqueStocks: Object.keys(stockCounts).length,
          multipleRecommendations,
          topBrokers,
          topRecommendation,
          avgRecommendationsPerDay: Math.round(combinedData.length / 15),
        };

        // Cache the results
        setAnalyticsCache(analyticsResult);
        setAnalyticsCacheTimestamp(now);
        setAnalyticsData(analyticsResult);
        
        console.log('Analytics data cached successfully');
      } catch (error) {
        console.warn('Failed to fetch analytics data');
      } finally {
        setAnalyticsLoading(false);
      }
    };

    fetchAnalytics();
  }, [selectedDate, analyticsCache, analyticsCacheTimestamp]);

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

  // Calculate stock recommendation counts
  const stockRecommendationCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    stockNewsWithLowerStocks?.forEach((news) => {
      counts[news.stock] = (counts[news.stock] || 0) + 1;
    });
    return counts;
  }, [stockNewsWithLowerStocks]);

  // Get stocks with multiple broker recommendations
  const stocksWithMultipleBrokers = useMemo(() => {
    return Object.entries(stockRecommendationCounts)
      .filter(([_, count]) => count > 1)
      .map(([stock, count]) => ({ stock, count }))
      .sort((a, b) => b.count - a.count);
  }, [stockRecommendationCounts]);

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
          {/* Date Picker Section */}
          <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
            <Typography
              variant="h6"
              fontWeight="bold"
              gutterBottom
              color="primary"
            >
              📅 Select Recommendations Date
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Choose a specific date to view recommendations (leave empty for latest available)
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <DatePickerComponent
                fromDateString={selectedDate}
                toDateString="" // We only need one date for news
                setFromDateString={setSelectedDate}
                setToDateString={() => {}} // No-op for to date
                singleDateMode={true} // Add this prop to DatePickerComponent if needed
              />
              {selectedDate && (
                <Chip
                  label="Clear Date"
                  onClick={() => setSelectedDate("")}
                  onDelete={() => setSelectedDate("")}
                  color="secondary"
                  variant="outlined"
                />
              )}
            </Box>
            {selectedDate && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Showing recommendations for: {new Date(selectedDate).toLocaleDateString()}
              </Typography>
            )}
          </Paper>

          {/* Analytics Banner - Only show when no specific date is selected */}
          {!selectedDate && analyticsData && !analyticsLoading && (
            <Paper
              elevation={3}
              sx={{
                p: 3,
                mb: 3,
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                color: "white",
                borderRadius: 3,
                position: "relative",
                overflow: "hidden",
                "&::before": {
                  content: '""',
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: "url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><circle cx=\"20\" cy=\"20\" r=\"2\" fill=\"white\" opacity=\"0.1\"/><circle cx=\"80\" cy=\"40\" r=\"1\" fill=\"white\" opacity=\"0.1\"/><circle cx=\"40\" cy=\"80\" r=\"1.5\" fill=\"white\" opacity=\"0.1\"/></svg>')",
                  pointerEvents: "none",
                },
              }}
            >
              <Box sx={{ position: "relative", zIndex: 1 }}>
                <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                  <LightbulbIcon sx={{ mr: 1, fontSize: 28 }} />
                  <Typography variant="h5" fontWeight="bold">
                    💡 Did You Know? - Last 15 Days Insights
                  </Typography>
                  {analyticsCacheTimestamp && (
                    <Chip
                      label="Cached"
                      size="small"
                      sx={{
                        ml: 2,
                        backgroundColor: "rgba(255, 255, 255, 0.2)",
                        color: "white",
                        fontSize: "0.7rem",
                      }}
                    />
                  )}
                </Box>
                
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Box sx={{ textAlign: "center" }}>
                      <AnalyticsIcon sx={{ fontSize: 40, mb: 1, opacity: 0.9 }} />
                      <Typography variant="h3" fontWeight="bold">
                        {analyticsData.totalRecommendations}
                      </Typography>
                      <Typography variant="body1" sx={{ opacity: 0.9 }}>
                        Total Recommendations
                      </Typography>
                      <Typography variant="caption" sx={{ opacity: 0.7 }}>
                        ~{analyticsData.avgRecommendationsPerDay} per day
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Box sx={{ textAlign: "center" }}>
                      <InsightsIcon sx={{ fontSize: 40, mb: 1, opacity: 0.9 }} />
                      <Typography variant="h3" fontWeight="bold">
                        {analyticsData.uniqueStocks}
                      </Typography>
                      <Typography variant="body1" sx={{ opacity: 0.9 }}>
                        Unique Stocks Covered
                      </Typography>
                      <Typography variant="caption" sx={{ opacity: 0.7 }}>
                        Across all brokers
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Box sx={{ textAlign: "center" }}>
                      <StarIcon sx={{ fontSize: 40, mb: 1, opacity: 0.9 }} />
                      <Typography variant="h3" fontWeight="bold">
                        {analyticsData.multipleRecommendations.length}
                      </Typography>
                      <Typography variant="body1" sx={{ opacity: 0.9 }}>
                        Consensus Picks
                      </Typography>
                      <Typography variant="caption" sx={{ opacity: 0.7 }}>
                        3+ broker recommendations
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {analyticsData.multipleRecommendations.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      🔥 Hot Consensus Picks (3+ Brokers):
                    </Typography>
                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                      {analyticsData.multipleRecommendations.slice(0, 6).map(([stock, count]: [string, number]) => (
                        <Chip
                          key={stock}
                          label={`${stock} (${count})`}
                          sx={{
                            backgroundColor: "rgba(255, 255, 255, 0.2)",
                            color: "white",
                            fontWeight: "bold",
                            "&:hover": {
                              backgroundColor: "rgba(255, 255, 255, 0.3)",
                            },
                          }}
                        />
                      ))}
                      {analyticsData.multipleRecommendations.length > 6 && (
                        <Chip
                          label={`+${analyticsData.multipleRecommendations.length - 6} more`}
                          sx={{
                            backgroundColor: "rgba(255, 255, 255, 0.1)",
                            color: "white",
                            border: "1px solid rgba(255, 255, 255, 0.3)",
                          }}
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </Box>
                )}

                <Box sx={{ mt: 3, display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 2 }}>
                  <Box>
                    <Typography variant="body2" sx={{ opacity: 0.8 }}>
                      Most Active Broker:
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {analyticsData.topBrokers[0]?.[0]} ({analyticsData.topBrokers[0]?.[1]} recommendations)
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" sx={{ opacity: 0.8 }}>
                      Most Common Recommendation:
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {analyticsData.topRecommendation?.[0]} ({analyticsData.topRecommendation?.[1]} times)
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ mt: 2, textAlign: "center" }}>
                  <Typography variant="caption" sx={{ opacity: 0.7, fontStyle: "italic" }}>
                    💡 Tip: Stocks with multiple broker consensus often show stronger momentum
                    {analyticsCacheTimestamp && (
                      <span> • Data refreshes every 15 minutes</span>
                    )}
                  </Typography>
                </Box>
              </Box>
            </Paper>
          )}

          {/* Loading state for analytics - show different message for cached vs fresh */}
          {!selectedDate && analyticsLoading && (
            <Paper elevation={2} sx={{ p: 3, mb: 3, textAlign: "center" }}>
              <CircularProgress size={24} sx={{ mr: 2 }} />
              <Typography variant="body1" component="span">
                {analyticsCache ? "Refreshing analytics..." : "Analyzing last 15 days of recommendations..."}
              </Typography>
            </Paper>
          )}

          {/* Multiple Brokers Highlight Section - Only for current day */}
          {stocksWithMultipleBrokers.length > 0 && (
            <Paper
              elevation={2}
              sx={{
                p: 3,
                mb: 3,
                background: "linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%)",
                border: "2px solid #ffc107",
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <StarIcon sx={{ color: "#f39c12", mr: 1 }} />
                <Typography
                  variant="h6"
                  fontWeight="bold"
                  color="#e67e22"
                >
                  🔥 Today's Hot Picks - Multiple Broker Consensus
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {selectedDate ? `Stocks with multiple recommendations for ${new Date(selectedDate).toLocaleDateString()}` : "Today's stocks with recommendations from multiple brokers are highlighted below"}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {stocksWithMultipleBrokers.slice(0, 10).map(({ stock, count }) => (
                  <Chip
                    key={stock}
                    icon={<TrendingUpIcon />}
                    label={`${stock} (${count})`}
                    color="warning"
                    variant="filled"
                    sx={{
                      fontWeight: "bold",
                      fontSize: "0.875rem",
                      "& .MuiChip-icon": {
                        color: "#e67e22",
                      },
                    }}
                  />
                ))}
                {stocksWithMultipleBrokers.length > 10 && (
                  <Chip
                    label={`+${stocksWithMultipleBrokers.length - 10} more`}
                    color="default"
                    variant="outlined"
                  />
                )}
              </Box>
            </Paper>
          )}

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
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: 1,
                          }}
                        >
                          <Typography
                            variant="subtitle1"
                            sx={{ fontWeight: "bold" }}
                          >
                            Stock
                          </Typography>
                          <Tooltip
                            title="Stocks with multiple broker recommendations are highlighted in yellow"
                            arrow
                          >
                            <GroupIcon
                              sx={{
                                fontSize: 16,
                                color: "text.secondary",
                              }}
                            />
                          </Tooltip>
                        </Box>
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
                      chunkedStockNews?.map((news, index) => {
                        const isMultipleBrokers = stockRecommendationCounts[news.stock] > 1;
                        return (
                          <NewsRow
                            key={`${news.stock}-${news.broker}-${index}`}
                            news={news}
                            index={index}
                            stockCounts={stockRecommendationCounts}
                            isMultipleBrokers={isMultipleBrokers}
                          />
                        );
                      })}
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
