import { IHeader, ItemType } from "./StockTable";
import { round_off } from "./Utils";

export const mainTableHeader: IHeader[] = [
    {
      display: 'S.No.',
      key: 'rank'
    },
    {
      display: 'Stock',
      key: 'stock',
      cellTemplate: (item: ItemType) => <td className='stock-name'>{item}</td>
    },
    {
      display: 'Symbol',
      key: 'symbol',
      cellTemplate: (item: ItemType) => <td className='stock-symbol'>{item}</td>
    },
    {
      display: 'Price',
      key: 'price',
      cellTemplate: (item: ItemType) => <td className='values'>{round_off(item as number)}</td>
    },
    {
      display: 'Weight',
      key: 'weight',
      cellTemplate: (item: ItemType) => <td className='values'>{round_off(item as number)}</td>
    },
    {
      display: 'Shares',
      key: 'shares',
      cellTemplate: (item: ItemType) => <td className='values'>{round_off(item as number)}</td>
    },
    {
      display: 'Investment',
      key: 'investment',
      cellTemplate: (item: ItemType) => <td className='values'>{round_off(item as number)}</td>
    },
    {
      display: 'Score',
      key: 'composite_score',
      cellTemplate: (item: ItemType) => <td className='values'>{round_off(item as number)}</td>
    }
  ];
  
export const rebalanceTableHeader: IHeader[] = [
    {
      display: 'S.No.',
      key: 'rank'
    },
    {
      display: 'Symbol',
      key: 'symbol',
      cellTemplate: (item: ItemType) => <td className='stock-symbol'>{item}</td>
    },
    {
      display: 'Amount',
      key: 'amount',
      cellTemplate: (item: ItemType) => {
        // if capital incurred is negative, then its profit, use the .profit className else .loss
        const className = item as number < 0 ? 'profit' : 'loss';
        return <td className={className}>{round_off(item as number)}</td>;
      }
    },
    {
      display: 'Shares',
      key: 'shares'
    },
    {
      display: 'Action',
      key: 'shares',
      cellTemplate: (item: ItemType) => {
        // determin hold, buy or sell
        const action = (item as number) === 0 ? 'Hold' : ((item as number) > 0 ? 'Buy' : 'Sell');
        return <td className={action}>{action}</td>;
      }
    }
  ];