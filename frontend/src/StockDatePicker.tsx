
import React, { useState } from "react";
import DatePicker from "react-datepicker";

import "react-datepicker/dist/react-datepicker.css";

interface IDatePickerProps {
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

export const StockDatePicker: React.FC<IDatePickerProps> = ({ initialDate, onDateChange, startDate, endDate }) => {
    const [selectedDate, setSelectedDate] = useState<Date | null>(initialDate != '' ? parseDateString(initialDate) : null);

    const isWeekday = (date: Date) => {
        const day = date.getDay();
        return day !== 0 && day !== 6;
    };

    return (
        <DatePicker
            onChange={(date: Date) => {

                // convert date to IST timezone
                const selected_date = new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toISOString().split('T')[0];

                onDateChange(selected_date);
                setSelectedDate(date);
            }}
            dateFormat='yyyy-MM-dd'
            placeholderText='Select a date'
            minDate={startDate ? parseDateString(startDate) : new Date('2023-10-04')}
            maxDate={endDate ? parseDateString(endDate) : new Date()}
            selected={selectedDate}
            filterDate={isWeekday}
        />
    );
};