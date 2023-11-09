
import React, { useState } from "react";
import DatePicker from "react-datepicker";

import "react-datepicker/dist/react-datepicker.css";

export const useStockDate = () => {
    const [selectedDate, setSelectedDate] = useState(new Date());

    const DatePickerComponent = () => (
        <DatePicker
            selected={selectedDate}
            onChange={date => setSelectedDate(date ?? new Date())}
            dateFormat='yyyy-MM-dd'
            placeholderText='Select a date'
        />
    );

    // convert to string
    const dateString = selectedDate.toISOString().split('T')[0];

    return { DatePickerComponent, dateString };
};