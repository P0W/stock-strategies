
import React, { useState } from "react";
import DatePicker from "react-datepicker";

import "react-datepicker/dist/react-datepicker.css";

export const StockDatePicker: React.FC<{ onDateChange: (date_string: string) => void }> = ({ onDateChange }) => {
    const [selectedDate, setSelectedDate] = useState(null);
    return (
        <DatePicker
            onChange={(date: Date | null) => {
                onDateChange(date ? date.toISOString().split('T')[0] : '');
            }}
            dateFormat='yyyy-MM-dd'
            placeholderText='Select a date'
            minDate={new Date('2023-10-04')}
            endDate={new Date('2023-11-10')}
            selected={selectedDate}
        />
    );
};