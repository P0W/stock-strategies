import React, { useEffect, useState } from "react";
import { Grid, TextField } from "@mui/material";

interface IDatePickerProps {
    label: string;
    initialDate: string;
    onDateChange: (date_string: string) => void;
    startDate?: string | null;
    endDate?: string | null;
}

const parseDateString = (dateStr: string): Date => {
    const dateRegex = /^(\d{4})-(\d{2})-(\d{2})$/;
    const match = dateStr.match(dateRegex);

    if (!match) {
        console.error(`Invalid date format. Use 'yyyy-mm-dd' ${dateStr}`);
        return new Date();
    }

    const [, year, month, day] = match.map(Number);
    const parsedDate = new Date(year, month - 1, day);

    // Check if the parsed date is valid
    if (isNaN(parsedDate.getTime())) {
        console.error("Invalid date values.");
        return new Date();
    }

    return parsedDate;
}

export const StockDatePicker: React.FC<IDatePickerProps> = ({ initialDate, onDateChange, startDate, endDate, label }) => {
    const [selectedDate, setSelectedDate] = useState<Date | null>(initialDate != '' ? parseDateString(initialDate) : null);

    const isWeekday = (date: Date) => {
        const day = date.getDay();
        return day !== 0 && day !== 6;
    };

    return (
        <TextField
            label={label}
            type="date"
            value={selectedDate ? selectedDate.toISOString().split('T')[0] : ''}
            onChange={(e) => {
                const date = new Date(e.target.value);
                // convert date to IST timezone
                const selected_date = new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toISOString().split('T')[0];
                onDateChange(selected_date);
                setSelectedDate(date);
            }}
            variant="outlined"
            InputLabelProps={{
                shrink: true,
            }}
            inputProps={{
                max: endDate ? parseDateString(endDate).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
                min: startDate ? parseDateString(startDate).toISOString().split('T')[0] : '2023-10-04',
            }}
        />
    );
};

interface DatePickerProps {
  fromDateString: string;
  toDateString: string;
  setFromDateString: (date: string) => void;
  setToDateString: (date: string) => void;
  singleDateMode?: boolean;
}

export const DatePickerComponent: React.FC<DatePickerProps> = ({
  fromDateString,
  toDateString,
  setFromDateString,
  setToDateString,
  singleDateMode = false,
}) => {
  const today = new Date().toISOString().split('T')[0];

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={singleDateMode ? 12 : 6}>
        <TextField
          label={singleDateMode ? "Select Date" : "From Date"}
          type="date"
          value={fromDateString}
          onChange={(e) => {
            const newFromDate = e.target.value;
            setFromDateString(newFromDate);
            
            // If to date is before the new from date, clear it
            if (toDateString && newFromDate > toDateString) {
              setToDateString("");
            }
          }}
          fullWidth
          variant="outlined"
          InputLabelProps={{
            shrink: true,
          }}
          inputProps={{
            max: toDateString || today,
            min: '2023-10-04',
          }}
        />
      </Grid>
      {!singleDateMode && (
        <Grid item xs={12} md={6}>
          <TextField
            label="To Date"
            type="date"
            value={toDateString}
            onChange={(e) => setToDateString(e.target.value)}
            fullWidth
            variant="outlined"
            disabled={!fromDateString}
            InputLabelProps={{
              shrink: true,
            }}
            inputProps={{
              max: today,
              min: fromDateString,
            }}
          />
        </Grid>
      )}
    </Grid>
  );
};