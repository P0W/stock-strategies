import {
  IHeader,
  INifty200Data,
  IRebalanceData,
  IStockData,
  IToFromData,
  ItemType,
} from "./StockDataTypes";
import { round_off } from "./Utils";
import { Box, Link, TableCell, Tooltip, Typography } from "@mui/material";
import { blue, grey, green, red } from "@mui/material/colors";

const NumericCell = (item: ItemType) => {
  return (
    <TableCell key={`price-${item}`} style={{ textAlign: "center" }}>
      <Typography
        style={{ fontWeight: "bold", color: "#666666", fontSize: "1.2em" }}
      >
        ₹
        {new Intl.NumberFormat("en-IN", { minimumFractionDigits: 2 }).format(
          item as number
        )}
      </Typography>
    </TableCell>
  );
};

const SharesCell = (item: ItemType) => {
  return (
    <TableCell key={`shares-${item}`} style={{ textAlign: "center" }}>
      <Typography
        style={{ fontWeight: "bold", color: "#666666", fontSize: "1.2em" }}
      >
        {round_off(item as number)}
      </Typography>
    </TableCell>
  );
};

const RebalanceSharesCell = (
  item: ItemType,
  row?: IStockData | IRebalanceData | INifty200Data
) => {
  return (
    <TableCell key={`shares-${item}`} style={{ textAlign: "center" }}>
      <Typography
        style={{ fontWeight: "bold", color: "#666666", fontSize: "1.2em" }}
      >
        {round_off(item as number)}
        {row?.initial_shares !== 0 &&
          ` / ${round_off(row?.initial_shares as number)}`}
      </Typography>
    </TableCell>
  );
};

const SymbolCell = (
  item: ItemType,
  row?: IStockData | IRebalanceData | INifty200Data
) => {
  return (
    <TableCell key={`symbol-${item}`} style={{ textAlign: "center" }}>
      <Tooltip title={row?.stock || ""}>
        {row?.url ? (
          <Link
            href={row.url}
            style={{ color: blue[500], fontWeight: "bold" }}
            underline="none"
            target="_blank"
            rel="noopener"
          >
            {item}
          </Link>
        ) : (
          <Typography style={{ color: blue[500], fontWeight: "bold" }}>
            {item}
          </Typography>
        )}
      </Tooltip>
    </TableCell>
  );
};

const RankCell = (item: ItemType) => {
  return (
    <TableCell key={`rank-${item}`} style={{ textAlign: "center" }}>
      <Typography
        style={{ fontWeight: "lighter", color: "#666666", fontSize: "1.2em" }}
      >
        {item}
      </Typography>
    </TableCell>
  );
};

export const rebalanceTableHeader: IHeader[] = [
  {
    display: "S.No.",
    key: "rank",
    cellTemplate: RankCell,
  },
  {
    display: "Symbol",
    key: "symbol",
    cellTemplate: SymbolCell,
  },
  {
    display: "Amount",
    key: "amount",
    cellTemplate: (item: ItemType) => {
      // if capital incurred is negative, then its profit, use the .profit className else .loss
      // use profit, loss or nochange classnames
      const action =
        (item as number) === 0
          ? "nochange"
          : (item as number) < 0
          ? "profit"
          : "loss";
      const actionColor =
        (item as number) === 0
          ? grey[500]
          : (item as number) < 0
          ? green[500]
          : red[500];

      return (
        <TableCell key={`amount-${action}`} style={{ textAlign: "center" }}>
          <Typography style={{ color: actionColor, fontWeight: "bold" }}>
            ₹
            {new Intl.NumberFormat("en-IN", {
              minimumFractionDigits: 2,
            }).format(item as number)}
          </Typography>
        </TableCell>
      );
    },
  },
  {
    display: "Shares",
    key: "shares",
    cellTemplate: RebalanceSharesCell,
  },
  {
    display: "Action",
    key: "shares",
    cellTemplate: (item: ItemType, row) => {
      // determine hold, buy or sell
      const action =
        (item as number) === 0 ? "Hold" : (item as number) > 0 ? "Buy" : "Sell";
      const actionColor =
        (item as number) === 0
          ? grey[500]
          : (item as number) > 0
          ? green[500]
          : red[500];
      
          // Determine the partial sell or buy
          let partial_suffix = false;
          if (
            row?.initial_shares !== 0 && (item as number) !==0 &&
            (row?.initial_shares as number) !== Math.abs(item as number)
          ) {
            partial_suffix = true;
          }
      return (
        <TableCell key={`shares-${action}`} style={{ textAlign: "center" }}>
          <Typography style={{ color: actionColor, fontWeight: "bold" }}>
            {partial_suffix && "Partial "}
            {action}
          </Typography>
        </TableCell>
      );
    },
  },
];

export const nifty200TableHeader: IHeader[] = [
  {
    display: "Rank",
    key: "rank",
    cellTemplate: RankCell,
  },
  {
    display: "Symbol",
    key: "symbol",
    cellTemplate: SymbolCell,
  },
  {
    display: "Avg. price",
    key: "avg_price",
    cellTemplate: NumericCell,
  },
  {
    display: "Weight",
    key: "weight",
    cellTemplate: SharesCell,
  },
  {
    display: "Shares",
    key: "shares",
    cellTemplate: SharesCell,
  },
  {
    display: "Investment",
    key: "investment",
    cellTemplate: NumericCell,
  },
  {
    display: "Current Price",
    key: "price",
    cellTemplate: NumericCell,
  },
  {
    display: "Profit/Loss",
    key: "price",
    cellTemplate: (item: ItemType, row) => {
      const thisRow = row as IToFromData;
      const diff = ((item as number) - thisRow.avg_price) * thisRow.shares;
      const isLoss = diff < 0;
      return (
        <TableCell
          align="center"
          key={`pnl-diff-${isLoss ? "loss" : "profit"}`}
        >
          <Box
            style={{
              backgroundColor: isLoss ? red[50] : green[50], // Lighter shades for background
            }}
          >
            <Typography
              style={{
                color: isLoss ? red[500] : green[500],
                fontWeight: "bold",
              }}
            >
              ₹
              {new Intl.NumberFormat("en-IN", {
                minimumFractionDigits: 2,
              }).format(diff)}
            </Typography>
          </Box>
        </TableCell>
      );
    },
  },
  {
    display: "Change",
    key: "price",
    cellTemplate: (item: ItemType, row) => {
      const thisRow = row as IToFromData;
      const diff =
        (((item as number) - thisRow.avg_price) / thisRow.price) * 100;
      const isLoss = diff < 0;
      return (
        <TableCell align="center" key={`diff-${isLoss ? "loss" : "profit"}`}>
          <Box
            style={{
              backgroundColor: isLoss ? red[50] : green[50], // Lighter shades for background
              // padding: '0.5em',
            }}
          >
            <Typography
              style={{
                color: isLoss ? red[500] : green[500],
                fontWeight: "bold",
              }}
            >
              {round_off(diff)}
            </Typography>
          </Box>
        </TableCell>
      );
    },
  },
];
