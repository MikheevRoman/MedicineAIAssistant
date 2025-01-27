import React, { useState, useEffect } from "react";
import cl from "./DayRadio.module.css";
import { Title3, Footnote } from "../../../../textStyles/TextStyleComponents";
import ButtonForScroll from "../buttonForScroll/ButtonForScroll";
import { ReactComponent as IconLeft } from '../../../../vectorIcons/IconForBtnScrollLeft.svg';
import { ReactComponent as IconRight } from '../../../../vectorIcons/IconForBtnScrollRight.svg';
import { useCheckboxStore } from "../../../../store/CheckboxStore";
import fetchStore from "../../../../store/FetchStore";
import { observer } from "mobx-react-lite";

const DayRadio = observer(({
    calendarData,
    scrollSetMonthName,
    handleSetSelectedDate,
    selectedDate
}) => {
    const firstEnabledIndex = calendarData.findIndex(item => !item.isDisabled);

    const [selectedItem, setSelectedItem] = useState(firstEnabledIndex);
    // eslint-disable-next-line no-unused-vars
    const [scrollPixels, setScrollPixels] = useState(0);
    const [visibleItems, setVisibleItems] = useState([]);

    const checkboxStore = useCheckboxStore();

    const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

    const currentDate = new Date();
    const currentDay = currentDate.getDate();
    const currentMonth = currentDate.getMonth();
    const currentYear = currentDate.getFullYear();



    useEffect(() => { // нужно чтоб при возвращаении на страницу при выбранном дне листалось до выбранного дня
        if (checkboxStore.selectedDate != null) {
            const container = document.getElementById("scrollContainer");
            let selectedIndex;
            let scrollAmount;

            if (isMobileDevice) {
                selectedIndex = calendarData.findIndex((item) =>
                    item.day === checkboxStore.selectedDate.day &&
                    item.month === checkboxStore.selectedDate.month &&
                    item.year === checkboxStore.selectedDate.year
                );
                scrollAmount = selectedIndex * 54;
            } else {
                selectedIndex = calendarData.findIndex((item) =>
                    item.day === checkboxStore.selectedDate.day &&
                    item.month === checkboxStore.selectedDate.month &&
                    item.year === checkboxStore.selectedDate.year
                );
                selectedIndex = Math.floor(selectedIndex / 7);
                scrollAmount = selectedIndex * 319;
            }

            container.scrollLeft += scrollAmount;
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    useEffect(() => {
        // Найдите индекс в calendarData, который соответствует selectedDate из хранилища
        const index = calendarData.findIndex(item =>
            item.day === selectedDate.day &&
            item.month === selectedDate.month &&
            item.year === selectedDate.year
        );

        // Установите найденный индекс как начальное выбранное значение
        setSelectedItem(index !== -1 ? index : firstEnabledIndex);

        // Обновите видимые элементы
        const updatedVisibleItems = calendarData.map((item) => {
            const formattedDate = `${item.year}-${String(item.month + 1).padStart(2, '0')}-${String(item.day).padStart(2, '0')}`;
            const dayData = fetchStore.workedDaysData.find(day => day.date === formattedDate);

            // Проверяем, есть ли хотя бы один свободный слот в этот день
            const isFree = dayData ? dayData.recordingCells.some(slot => slot.status === "FREE") : false;

            // Если день находится в прошлом (до текущей даты), делаем его полупрозрачным
            const isPast =
                item.year < currentYear ||
                (item.year === currentYear && item.month < currentMonth) ||
                (item.year === currentYear && item.month === currentMonth && item.day < currentDay);

            return isFree && !isPast;
        });
        setVisibleItems(updatedVisibleItems);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [calendarData, selectedDate, firstEnabledIndex, currentYear, currentMonth, currentDay, fetchStore.workedDaysData]);


    const handleItemClick = (index) => {
        setSelectedItem(index);
        handleSetSelectedDate(index);
    };

    const handleScroll = (e) => {
        const scrolled = e.target.scrollLeft;
        setScrollPixels(scrolled);
        scrollSetMonthName(scrolled);
    };

    const handleBtnScroll = (direction) => {
        const container = document.getElementById("scrollContainer");
        const scrollAmount = direction === 'left' ? -319 : 319;
        container.scrollLeft += scrollAmount;
    };

    return (
        <div className={cl.container}>

            {!isMobileDevice && (
                <ButtonForScroll icon={IconLeft} handleBtnScroll={handleBtnScroll} direction={"left"} />
            )}

            <div className={cl.forScrollbarNone} >
                <div
                    id="scrollContainer"
                    className={cl.scrollContainer}
                    onScroll={handleScroll}
                >
                    {calendarData.map((item, index) => (
                        <label key={index} htmlFor={`day${index}`}>
                            <div className={cl.scrollDays} style={{ marginLeft: isMobileDevice ? '10px' : '1.5px' }}>
                                <div className={cl.scrollDay}>
                                    <input
                                        type="radio"
                                        id={`day${index}`}
                                        name="days"
                                        className={cl.radioButton}
                                        checked={selectedItem === index}
                                        onChange={() => handleItemClick(index)}
                                        disabled={item.isDisabled}
                                    />

                                    <div className={cl.dayContainer}>
                                        <Title3
                                            className={`${cl.numberOfDay} 
                                            ${!visibleItems[index] && !(selectedItem === index) ? cl.inactiveDay : ''} 
                                            ${item.day === currentDay && item.month === currentMonth && item.year === currentYear ? cl.currentDay : ''}`}
                                        >
                                            {item.day}
                                        </Title3>
                                    </div>
                                    <Footnote className={cl.dayOfWeek}>
                                        {item.shortDayOfWeek}
                                    </Footnote>
                                </div>
                            </div>
                        </label>
                    ))}
                </div>
            </div>

            {!isMobileDevice && (
                <ButtonForScroll icon={IconRight} handleBtnScroll={handleBtnScroll} direction={"right"} />
            )}

        </div>
    );
});

export default DayRadio;
