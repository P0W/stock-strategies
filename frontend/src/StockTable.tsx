import React from "react";
import { IStockData, SymbolRow } from "./SymbolRow";
import './StockTable.css';

export interface IHeader {
    display: string;
    key: string;
    cellTemplate?: (key: string, item: number) => React.ReactElement;
}

interface IStockTable {
    headers: IHeader[];
    toDateString: string;
    fromDateString: string;
}


const useData = (toDateString: string, fromDateString: string) => {
    const [toDateStocks, setToDateStocks] = React.useState([]);
    const [fromDateStocks, setFromDateStocks] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const cache = React.useRef<{ [key: string]: IStockData[] }>({});

    const fetchData = (endpoint: string, fromDate: string, toDate?: string) => {
        const urlEndPoint = toDate ? `/${endpoint}/${fromDate}/${toDate}` : `/${endpoint}/${fromDate}`;
        if (cache.current[urlEndPoint]) {
            return Promise.resolve(cache.current[urlEndPoint]);
        } else {
            return fetch(urlEndPoint)
                .then(res => res.json())
                .then(data => {
                    cache.current[urlEndPoint] = data[0];
                    return data[0];
                });
        }
    };


    React.useEffect(() => {
        setLoading(true);
        const toFetch = fetchData('portfolio', toDateString);
        const fromFetch = fetchData('portfolio', fromDateString);
        const nifty200Fetch = fetchData('nifty200', toDateString);
        const rebalanceFetch = fetchData('rebalance', toDateString, fromDateString);

        Promise.all([toFetch, fromFetch, nifty200Fetch, rebalanceFetch])
            .then(data => {
                setToDateStocks(data[0]);
                setFromDateStocks(data[1]);
                setLoading(false);
            })
            .catch(err => {
                console.log(err);
                setLoading(false);
            });
    }, [toDateString, fromDateString]);

    return { toDateStocks, fromDateStocks, loading };
};


export const StockTable: React.FC<IStockTable> = ({ headers, toDateString, fromDateString }): React.ReactElement => {
    const { toDateStocks, fromDateStocks, loading } = useData(toDateString, fromDateString);

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <table className="stock-table">
            <thead>
                <tr>
                    {headers?.map((header, index) => (
                        <th key={index}>{header.display}</th>
                    ))}
                </tr>
            </thead>

            <tbody>
                {toDateStocks?.map((stock, index) => (
                    <SymbolRow key={index} item={stock} rank={index + 1} headers={headers} />
                ))}
            </tbody>
        </table>
    );
};