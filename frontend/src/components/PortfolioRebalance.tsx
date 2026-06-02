import React, { useCallback, useMemo, useRef, useState } from "react";
import {
  Alert,
  AlertTitle,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  Link,
  Stack,
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
import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  IHolding,
  IRebalanceRow,
  IStockBalls,
  RebalanceAction,
} from "./StockDataTypes";

interface IProps {
  stockBalls: IStockBalls[];
}

interface IParseResult {
  holdings: IHolding[];
  warnings: string[];
}

// Normalize a ticker for matching. Keep "&" and "-" since valid NSE
// symbols contain them (e.g. M&M, M&MFIN, BAJAJ-AUTO).
const normalizeSymbol = (raw: string): string =>
  raw.replace(/\uFEFF/g, "").trim().toUpperCase();

// Parse an Indian-formatted number: strips currency, %, thousands commas.
const parseNum = (raw: string): number => {
  if (raw === undefined || raw === null) return NaN;
  const cleaned = raw
    .replace(/\uFEFF/g, "")
    .replace(/[₹%\s]/g, "")
    .replace(/,/g, "")
    .trim();
  if (cleaned === "" || cleaned === "-") return NaN;
  return parseFloat(cleaned);
};

// Quote-aware CSV parser -> array of rows of string fields.
const parseCsv = (text: string): string[][] => {
  const cleaned = text.replace(/^\uFEFF/, "");
  const rows: string[][] = [];
  let field = "";
  let row: string[] = [];
  let inQuotes = false;

  for (let i = 0; i < cleaned.length; i++) {
    const ch = cleaned[i];
    if (inQuotes) {
      if (ch === '"') {
        if (cleaned[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && cleaned[i + 1] === "\n") i++;
      row.push(field);
      rows.push(row);
      field = "";
      row = [];
    } else {
      field += ch;
    }
  }
  if (field !== "" || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  return rows;
};

const findColumn = (header: string[], needle: string): number =>
  header.findIndex((h) => h.toLowerCase().includes(needle));

// Parse a Smallcase CSV export into holdings. Skips the metadata rows
// above the constituents table and aggregates duplicate tickers.
const parseSmallcaseCsv = (text: string): IParseResult => {
  const warnings: string[] = [];
  const rows = parseCsv(text);

  const headerIdx = rows.findIndex(
    (r) =>
      r.some((c) => c.toLowerCase().includes("ticker")) &&
      r.some((c) => c.toLowerCase().includes("shares"))
  );

  if (headerIdx === -1) {
    throw new Error(
      "Could not find the holdings table. Make sure this is a Smallcase CSV export (it must contain a 'Ticker' and 'Shares' column)."
    );
  }

  const header = rows[headerIdx];
  const col = {
    name: findColumn(header, "name"),
    ticker: findColumn(header, "ticker"),
    price: findColumn(header, "current price"),
    avg: findColumn(header, "avg"),
    returns: findColumn(header, "returns"),
    weight: findColumn(header, "weight"),
    shares: findColumn(header, "shares"),
  };

  const bySymbol = new Map<string, IHolding>();
  let skipped = 0;

  for (let i = headerIdx + 1; i < rows.length; i++) {
    const r = rows[i];
    const ticker = col.ticker >= 0 ? normalizeSymbol(r[col.ticker] ?? "") : "";
    const shares = parseNum(r[col.shares] ?? "");

    // Stop / skip rows that are not holdings (blank line, footer, etc.)
    if (!ticker || isNaN(shares) || shares <= 0) {
      if (r.some((c) => c.trim() !== "")) skipped++;
      continue;
    }

    const currentPrice = parseNum(r[col.price] ?? "");
    const holding: IHolding = {
      stock: (r[col.name] ?? "").trim() || ticker,
      symbol: ticker,
      shares,
      currentPrice: isNaN(currentPrice) ? 0 : currentPrice,
      avgPrice: col.avg >= 0 ? parseNum(r[col.avg] ?? "") : NaN,
      returns: col.returns >= 0 ? parseNum(r[col.returns] ?? "") : NaN,
      weight: col.weight >= 0 ? parseNum(r[col.weight] ?? "") : NaN,
    };

    const existing = bySymbol.get(ticker);
    if (existing) {
      // Aggregate duplicate tickers (share-weighted current price).
      const totalShares = existing.shares + holding.shares;
      existing.currentPrice =
        (existing.currentPrice * existing.shares +
          holding.currentPrice * holding.shares) /
        (totalShares || 1);
      existing.shares = totalShares;
      warnings.push(`Aggregated duplicate rows for ${ticker}.`);
    } else {
      bySymbol.set(ticker, holding);
    }
  }

  if (skipped > 0) {
    warnings.push(`Skipped ${skipped} row(s) without a valid ticker/shares.`);
  }

  return { holdings: Array.from(bySymbol.values()), warnings };
};

const ACTION_COLOR: Record<
  RebalanceAction,
  "success" | "error" | "warning" | "info" | "default"
> = {
  HOLD: "success",
  SELL: "error",
  BUY: "warning",
  ADD: "info",
  TRIM: "warning",
  REVIEW: "default",
};

const ACTION_LABEL: Record<RebalanceAction, string> = {
  HOLD: "HOLD",
  SELL: "SELL OFF",
  BUY: "BUY",
  ADD: "ADD",
  TRIM: "TRIM",
  REVIEW: "REVIEW",
};

const ScoreBalls: React.FC<{ scoreCard: { [k: string]: string } | null }> = ({
  scoreCard,
}) => {
  if (!scoreCard) return <span>—</span>;
  return (
    <Stack direction="row" spacing={0.5} justifyContent="center" flexWrap="wrap">
      {Object.keys(scoreCard).map((key) => (
        <Tooltip key={key} title={`${key}: ${scoreCard[key]}`} arrow>
          <Avatar
            sx={{
              bgcolor: scoreCard[key],
              color: scoreCard[key] === "yellow" ? "black" : "white",
              width: 22,
              height: 22,
              fontSize: 12,
              fontWeight: "bold",
            }}
          >
            {key[0].toUpperCase()}
          </Avatar>
        </Tooltip>
      ))}
    </Stack>
  );
};

export const PortfolioRebalance: React.FC<IProps> = ({ stockBalls }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [holdings, setHoldings] = useState<IHolding[]>([]);
  const [fileName, setFileName] = useState<string>("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [targetSize, setTargetSize] = useState<number>(10);

  // Rank every scorecard stock (1-based) by composite score, defensively
  // sorted so we never rely on backend ordering or UI sort state.
  const rankMap = useMemo(() => {
    const ranked = [...stockBalls].sort(
      (a, b) => b.composite_score - a.composite_score
    );
    const map = new Map<
      string,
      { rank: number; data: IStockBalls }
    >();
    ranked.forEach((s, idx) => {
      map.set(normalizeSymbol(s.symbol), { rank: idx + 1, data: s });
    });
    return map;
  }, [stockBalls]);

  const handleFile = useCallback(
    (file: File) => {
      setError(null);
      setWarnings([]);
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = String(e.target?.result ?? "");
          const result = parseSmallcaseCsv(text);
          if (result.holdings.length === 0) {
            throw new Error("No holdings were found in the file.");
          }
          setHoldings(result.holdings);
          setWarnings(result.warnings);
          setFileName(file.name);
          setTargetSize(result.holdings.length);
        } catch (err) {
          setHoldings([]);
          setFileName("");
          setError(err instanceof Error ? err.message : "Failed to parse file.");
        }
      };
      reader.onerror = () => setError("Could not read the file.");
      reader.readAsText(file);
    },
    []
  );

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  };

  const totalValue = useMemo(
    () => holdings.reduce((sum, h) => sum + h.shares * h.currentPrice, 0),
    [holdings]
  );

  const targetPerStock = targetSize > 0 ? totalValue / targetSize : 0;

  // Build the rebalance plan as a single action list: for each holding decide
  // hold/adjust/sell, and add new top-N buys. Quantities target equal weight.
  const { rows, unmatched } = useMemo(() => {
    const heldSymbols = new Set(holdings.map((h) => h.symbol));
    const unmatchedList: string[] = [];
    const plan: IRebalanceRow[] = [];

    const targetSharesFor = (price: number | null): number =>
      price && price > 0 ? Math.max(1, Math.round(targetPerStock / price)) : 0;

    // 1) Existing holdings.
    holdings.forEach((h) => {
      const match = rankMap.get(h.symbol);
      const price = h.currentPrice || null;
      const value = h.shares * h.currentPrice;

      if (!match) {
        unmatchedList.push(h.symbol);
        plan.push({
          symbol: h.symbol,
          stock: h.stock,
          action: "REVIEW",
          rank: null,
          composite_score: null,
          score_card: null,
          link: null,
          shares: h.shares,
          price,
          value,
          targetShares: h.shares,
          deltaShares: 0,
          deltaAmount: 0,
        });
        return;
      }

      const inTarget = match.rank <= targetSize;
      const redFlag = match.data.score_card?.["Red flags"] === "red";

      if (!inTarget || redFlag) {
        // Exit completely.
        plan.push({
          symbol: h.symbol,
          stock: match.data.stock || h.stock,
          action: "SELL",
          rank: match.rank,
          composite_score: match.data.composite_score,
          score_card: match.data.score_card,
          link: match.data.link,
          shares: h.shares,
          price,
          value,
          targetShares: 0,
          deltaShares: -h.shares,
          deltaAmount: -value,
        });
        return;
      }

      // Keep, but adjust quantity toward equal weight.
      const targetShares = price ? targetSharesFor(price) : h.shares;
      const deltaShares = targetShares - h.shares;
      const action: RebalanceAction =
        deltaShares > 0 ? "ADD" : deltaShares < 0 ? "TRIM" : "HOLD";
      plan.push({
        symbol: h.symbol,
        stock: match.data.stock || h.stock,
        action,
        rank: match.rank,
        composite_score: match.data.composite_score,
        score_card: match.data.score_card,
        link: match.data.link,
        shares: h.shares,
        price,
        value,
        targetShares,
        deltaShares,
        deltaAmount: deltaShares * (h.currentPrice || 0),
      });
    });

    // 2) New entries: top-N scorecard stocks we don't already hold.
    rankMap.forEach((entry, symbol) => {
      if (entry.rank > targetSize || heldSymbols.has(symbol)) return;
      const price = entry.data.price ?? null;
      const targetShares = targetSharesFor(price);
      plan.push({
        symbol,
        stock: entry.data.stock,
        action: "BUY",
        rank: entry.rank,
        composite_score: entry.data.composite_score,
        score_card: entry.data.score_card,
        link: entry.data.link,
        shares: 0,
        price,
        value: 0,
        targetShares,
        deltaShares: targetShares,
        deltaAmount: price ? targetShares * price : 0,
      });
    });

    // Group HOLD (incl. ADD/TRIM) -> SELL -> BUY -> REVIEW, then by rank.
    const groupOrder: Record<RebalanceAction, number> = {
      HOLD: 0,
      ADD: 0,
      TRIM: 0,
      SELL: 1,
      BUY: 2,
      REVIEW: 3,
    };
    plan.sort(
      (a, b) =>
        groupOrder[a.action] - groupOrder[b.action] ||
        (a.rank ?? 9999) - (b.rank ?? 9999)
    );
    return { rows: plan, unmatched: unmatchedList };
  }, [holdings, rankMap, targetSize, targetPerStock]);

  const sellProceeds = useMemo(
    () =>
      rows
        .filter((r) => r.deltaAmount < 0)
        .reduce((s, r) => s - r.deltaAmount, 0),
    [rows]
  );
  const buyCost = useMemo(
    () =>
      rows
        .filter((r) => r.deltaAmount > 0)
        .reduce((s, r) => s + r.deltaAmount, 0),
    [rows]
  );
  const holdCount = rows.filter(
    (r) => r.action === "HOLD" || r.action === "ADD" || r.action === "TRIM"
  ).length;
  const sellCount = rows.filter((r) => r.action === "SELL").length;
  const buyCount = rows.filter((r) => r.action === "BUY").length;
  const reviewCount = rows.filter((r) => r.action === "REVIEW").length;

  // Build a plain-English summary, e.g.
  // "You are buying 8 stocks, holding 1 stock and selling 7 stocks."
  const summarySentence = useMemo(() => {
    const noun = (n: number) => (n === 1 ? "stock" : "stocks");
    const parts: string[] = [];
    if (buyCount > 0) parts.push(`buying ${buyCount} ${noun(buyCount)}`);
    if (holdCount > 0) parts.push(`holding ${holdCount} ${noun(holdCount)}`);
    if (sellCount > 0) parts.push(`selling ${sellCount} ${noun(sellCount)}`);

    let sentence = "You are ";
    if (parts.length === 0) {
      sentence += "making no changes";
    } else if (parts.length === 1) {
      sentence += parts[0];
    } else {
      sentence +=
        parts.slice(0, -1).join(", ") + " and " + parts[parts.length - 1];
    }
    sentence += ".";
    if (reviewCount > 0) {
      sentence += ` ${reviewCount} ${noun(
        reviewCount
      )} need manual review (not in the scorecard).`;
    }
    return sentence;
  }, [buyCount, holdCount, sellCount, reviewCount]);

  const fmt = (n: number) =>
    "₹" + Math.round(n).toLocaleString("en-IN");

  const renderActionRow = (r: IRebalanceRow) => (
    <TableRow key={`${r.action}-${r.symbol}`} hover>
      <TableCell align="center">{r.rank ?? "—"}</TableCell>
      <TableCell>
        {r.link ? (
          <Link href={r.link} target="_blank" rel="noopener noreferrer">
            <strong>{r.symbol}</strong>
          </Link>
        ) : (
          <strong>{r.symbol}</strong>
        )}
        <Typography variant="caption" display="block" color="text.secondary">
          {r.stock}
        </Typography>
      </TableCell>
      <TableCell align="center">
        {r.composite_score !== null
          ? (r.composite_score * 100).toFixed(1)
          : "—"}
      </TableCell>
      <TableCell align="center">
        <ScoreBalls scoreCard={r.score_card} />
      </TableCell>
      <TableCell align="center">{r.shares || "—"}</TableCell>
      <TableCell align="center">
        <strong>{r.action === "REVIEW" ? "—" : r.targetShares}</strong>
      </TableCell>
      <TableCell align="center">
        <Chip
          size="small"
          label={ACTION_LABEL[r.action]}
          color={ACTION_COLOR[r.action]}
          sx={{ fontWeight: "bold" }}
        />
      </TableCell>
      <TableCell align="right">
        {r.action === "SELL" && (
          <Typography variant="body2" color="error">
            Sell all {r.shares} (≈{fmt(r.value)})
          </Typography>
        )}
        {r.action === "BUY" &&
          (r.targetShares > 0 ? (
            <Typography variant="body2" color="warning.main">
              Buy {r.targetShares} (≈{fmt(r.deltaAmount)})
            </Typography>
          ) : (
            <Typography variant="caption" color="text.secondary">
              price unavailable
            </Typography>
          ))}
        {r.action === "ADD" && (
          <Typography variant="body2" sx={{ color: "info.main" }}>
            Buy {r.deltaShares} more (≈{fmt(r.deltaAmount)})
          </Typography>
        )}
        {r.action === "TRIM" && (
          <Typography variant="body2" color="warning.main">
            Sell {Math.abs(r.deltaShares)} (≈{fmt(Math.abs(r.deltaAmount))})
          </Typography>
        )}
        {r.action === "HOLD" && (
          <Typography variant="caption" color="text.secondary">
            Keep as is ({fmt(r.value)})
          </Typography>
        )}
        {r.action === "REVIEW" && (
          <Typography variant="caption" color="text.secondary">
            Not in scorecard — decide manually
          </Typography>
        )}
      </TableCell>
    </TableRow>
  );

  const SummaryStat: React.FC<{ label: string; value: string; color?: string }> = ({
    label,
    value,
    color,
  }) => (
    <Grid item xs={6} sm={4} md={2}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h6" sx={{ color: color ?? "text.primary" }}>
        {value}
      </Typography>
    </Grid>
  );

  return (
    <Card elevation={3} sx={{ borderRadius: 2, overflow: "hidden", mb: 4 }}>
      <Box
        sx={{
          p: 2,
          background: "linear-gradient(45deg, #43A047 30%, #66BB6A 90%)",
          color: "white",
        }}
      >
        <Typography variant="h4" component="h2" gutterBottom>
          Rebalance Your Smallcase
        </Typography>
        <Typography variant="subtitle1">
          Upload your Smallcase CSV export to get scorecard-driven BUY / SELL /
          HOLD suggestions (top-{targetSize} equal weight).
        </Typography>
      </Box>
      <CardContent>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          alignItems={{ xs: "stretch", sm: "center" }}
          mb={2}
        >
          <Button
            variant="contained"
            startIcon={<UploadFileIcon />}
            onClick={() => fileInputRef.current?.click()}
          >
            Upload Smallcase CSV
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            hidden
            onChange={onInputChange}
          />
          {fileName && (
            <Typography variant="body2" color="text.secondary">
              Loaded: <strong>{fileName}</strong>
            </Typography>
          )}
          {holdings.length > 0 && (
            <TextField
              label="Target portfolio size"
              type="number"
              size="small"
              value={targetSize}
              onChange={(e) =>
                setTargetSize(
                  Math.max(
                    1,
                    Math.min(
                      stockBalls.length || 1,
                      parseInt(e.target.value || "1", 10) || 1
                    )
                  )
                )
              }
              inputProps={{ min: 1, max: stockBalls.length }}
              sx={{ width: 180 }}
            />
          )}
        </Stack>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {holdings.length === 0 && !error && (
          <Alert severity="info">
            In Smallcase, open your Stock-Balls smallcase → Export to CSV, then
            upload it here. Your holdings are matched against the scorecard above
            to suggest which to sell, hold, and buy. Nothing is uploaded to a
            server — parsing happens in your browser.
          </Alert>
        )}

        {holdings.length > 0 && (
          <>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <SummaryStat label="Holdings" value={String(holdings.length)} />
              <SummaryStat label="Portfolio value" value={fmt(totalValue)} />
              <SummaryStat label="Target / stock" value={fmt(targetPerStock)} />
              <SummaryStat
                label="Hold"
                value={String(holdCount)}
                color="#2e7d32"
              />
              <SummaryStat
                label="Sell"
                value={`${sellCount} (${fmt(sellProceeds)})`}
                color="#d32f2f"
              />
              <SummaryStat
                label="Buy / Add"
                value={`${buyCount} new (${fmt(buyCost)})`}
                color="#ed6c02"
              />
            </Grid>

            <Alert
              severity="success"
              icon={false}
              sx={{
                mb: 2,
                "& .MuiAlert-message": { width: "100%" },
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: "bold" }}>
                {summarySentence}
              </Typography>
            </Alert>

            {(warnings.length > 0 || unmatched.length > 0) && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                <AlertTitle>Review</AlertTitle>
                {unmatched.length > 0 && (
                  <div>
                    Not found in scorecard (decide manually):{" "}
                    <strong>{unmatched.join(", ")}</strong>
                  </div>
                )}
                {warnings.map((w, i) => (
                  <div key={i}>{w}</div>
                ))}
              </Alert>
            )}

            <Alert severity="info" sx={{ mb: 2 }} icon={false}>
              Net cash if executed: <strong>{fmt(sellProceeds - buyCost)}</strong>{" "}
              ({fmt(sellProceeds)} from sells/trims − {fmt(buyCost)} for buys/adds).
              Your past rebalances are roughly capital-neutral, so adjust target
              size or quantities to match available cash.
            </Alert>

            <Typography variant="h6" gutterBottom>
              Action plan
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Hold = keep, Add/Trim = adjust quantity to equal weight, Sell off =
              exit, Buy = new entry. "Target" is the quantity to end up holding.
            </Typography>
            <TableContainer>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell align="center">Rank</TableCell>
                    <TableCell>Stock</TableCell>
                    <TableCell align="center">Score</TableCell>
                    <TableCell align="center">Score Card</TableCell>
                    <TableCell align="center">Current Qty</TableCell>
                    <TableCell align="center">Target Qty</TableCell>
                    <TableCell align="center">Action</TableCell>
                    <TableCell align="right">What to do</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(() => {
                    const groupLabel = (a: IRebalanceRow["action"]): string =>
                      a === "SELL"
                        ? "Sell off"
                        : a === "BUY"
                        ? "Buy new"
                        : a === "REVIEW"
                        ? "Review manually"
                        : "Hold & adjust";
                    let lastGroup = "";
                    const out: React.ReactNode[] = [];
                    rows.forEach((r) => {
                      const g = groupLabel(r.action);
                      if (g !== lastGroup) {
                        lastGroup = g;
                        out.push(
                          <TableRow key={`group-${g}`}>
                            <TableCell
                              colSpan={8}
                              sx={{
                                bgcolor: "action.hover",
                                fontWeight: "bold",
                                textTransform: "uppercase",
                                letterSpacing: 0.5,
                              }}
                            >
                              {g}
                            </TableCell>
                          </TableRow>
                        );
                      }
                      out.push(renderActionRow(r));
                    });
                    return out;
                  })()}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </CardContent>
    </Card>
  );
};
