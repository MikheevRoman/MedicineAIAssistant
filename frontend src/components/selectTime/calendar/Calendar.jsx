import React, { useEffect } from "react";
import cl from "./Calendar.module.css";
import { useState } from "react";
import { HeadLineSemibold, HeadLineMonoNumbers } from "../../../textStyles/TextStyleComponents";
import DayRadio from "./dayRadio/DayRadio";
import FreeTime from "../freeTime/FreeTime";
import { observer } from 'mobx-react-lite';
import { useCheckboxStore } from "../../../store/CheckboxStore";

const Calendar = observer(() => {

  const currentDate = new Date();
  const currentMonth = currentDate.getMonth();
  const currentDay = currentDate.getDate();
  const currentYear = currentDate.getFullYear();
  const tg = window.Telegram.WebApp;

  const monthNames = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];


  const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

  const checkboxStore = useCheckboxStore();

  const getDaysInMonth = (year, month) => {
    return new Date(year, month + 1, 0).getDate();
  };

  // const [monthName, setMonthName] = useState(monthNames[currentMonth]);
  const [monthNumber, setMonthNumber] = useState(currentMonth);
  const [yearNumber, setYearNumber] = useState(currentYear)

  const [selectedDate, setSelectedDate] = useState({
    day: currentDay,
    month: currentMonth,
    year: currentYear
  });

  useEffect(() => {
    if (checkboxStore.selectedDate) {
      setSelectedDate(checkboxStore.selectedDate);
    } else {
      checkboxStore.setSelectedDate({
        day: currentDay,
        month: currentMonth,
        year: currentYear
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [checkboxStore, currentDay]);

  // const scrollSetMonthName = useCallback(_.throttle((scrolledPixels) => {
  //   let totalPixelsForCurrentMonth = countOfDayInThisMonth * pixelsForOneDay;
  //   let monthIndex = currentMonth;
  //   let accumulatedPixels = 0;
  //   if (scrolledPixels < 0) {
  //     scrolledPixels = 0;
  //   }

  //   // Пока прокрученные пиксели больше, чем на один месяц, продолжаем итерировать
  //   while (scrolledPixels > totalPixelsForCurrentMonth) {
  //     scrolledPixels -= totalPixelsForCurrentMonth;
  //     monthIndex = (monthIndex + 1) % 12; // Переходим к следующему месяцу
  //     accumulatedPixels += totalPixelsForCurrentMonth; // Накапливаем пиксели
  //     totalPixelsForCurrentMonth = getDaysInMonth(currentYear, monthIndex) * pixelsForOneDay;
  //   }

  //   // Если прокрутили назад
  //   while (scrolledPixels < -accumulatedPixels) {

  //     monthIndex = monthIndex - 1 < 0 ? 11 : monthIndex - 1; // Переходим к предыдущему месяцу
  //     totalPixelsForCurrentMonth = getDaysInMonth(currentYear, monthIndex) * pixelsForOneDay;
  //     accumulatedPixels -= totalPixelsForCurrentMonth; // Вычитаем пиксели
  //   }

  //   setMonthNumber(monthIndex); // Обновляем состояние месяца
  // }, 1000), []);



  const getShortDayOfWeek = (year, month, day) => {
    const date = new Date(year, month, day);
    return new Intl.DateTimeFormat('ru-RU', { weekday: 'short' }).format(date).toUpperCase();
  };

  let countOnDisabledDay = 0;

  const generateCalendarData = (startYear, startMonth, startDay, activeCount) => {
    const calendarData = [];
    let year = startYear;
    let month = startMonth;
    let day = startDay;
    let activeDaysGenerated = 0;

    if (!isMobileDevice) {
      let date = new Date(year, month, day);
      let dayOfWeek = date.getDay();
      let daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
      for (let i = daysToMonday; i > 0; i--) {
        countOnDisabledDay++;
        let pastDate = new Date(year, month, day - i);
        calendarData.push({
          day: pastDate.getDate(),
          shortDayOfWeek: getShortDayOfWeek(pastDate.getFullYear(), pastDate.getMonth(), pastDate.getDate()),
          month: pastDate.getMonth(),
          year: pastDate.getFullYear(),
          isDisabled: true
        });
      }
    }

    while (activeDaysGenerated < activeCount) {
      const daysInMonth = getDaysInMonth(year, month);
      for (; day <= daysInMonth && activeDaysGenerated < activeCount; day++) {
        const shortDayOfWeek = getShortDayOfWeek(year, month, day);
        calendarData.push({ day, shortDayOfWeek, month, year, isDisabled: false });
        activeDaysGenerated++;
      }
      day = 1;
      month = (month + 1) % 12;
      if (month === 0) year++;
    }

    if (!isMobileDevice) {
      let lastDay = calendarData[calendarData.length - 1];
      let lastDate = new Date(lastDay.year, lastDay.month, lastDay.day);
      let lastDayOfWeek = lastDate.getDay();
      let daysToSunday = lastDayOfWeek === 0 ? 0 : 7 - lastDayOfWeek;
      for (let i = 1; i <= daysToSunday; i++) {
        let nextDate = new Date(lastDay.year, lastDay.month, lastDay.day + i);
        calendarData.push({
          day: nextDate.getDate(),
          shortDayOfWeek: getShortDayOfWeek(nextDate.getFullYear(), nextDate.getMonth(), nextDate.getDate()),
          month: nextDate.getMonth(),
          year: nextDate.getFullYear(),
          isDisabled: true
        });
      }
    }

    return calendarData;
  };

  const calendarData = generateCalendarData(currentYear, currentMonth, currentDay, 60);


  let pixelsForOneDay = 45.5;
  if (isMobileDevice) pixelsForOneDay = 54;

  const countOfDayInThisMonth = (getDaysInMonth(currentYear, currentMonth) - currentDay + 1 + countOnDisabledDay) * pixelsForOneDay
  const countOfDayInNext1Month = (getDaysInMonth(currentYear, currentMonth + 1)) * pixelsForOneDay + countOfDayInThisMonth
  const countOfDayInNext2Month = (getDaysInMonth(currentYear, currentMonth + 2)) * pixelsForOneDay + countOfDayInNext1Month

  let temproraryMonthNumber;
  let temproraryYearNumber = currentYear;

  const scrollSetMonthName = (scrolled) => {
    if (scrolled >= countOfDayInNext2Month) {
      temproraryMonthNumber = currentMonth + 3;
    } else if (scrolled >= countOfDayInNext1Month) {
      temproraryMonthNumber = currentMonth + 2;
    } else if (scrolled >= countOfDayInThisMonth) {
      temproraryMonthNumber = currentMonth + 1;
    } else if (scrolled < countOfDayInThisMonth) {
      temproraryMonthNumber = currentMonth;
    }

    if (temproraryMonthNumber >= 12) {
      temproraryYearNumber = currentYear + 1
      temproraryMonthNumber -= 12
    }

    if (temproraryMonthNumber !== monthNumber) {
      setMonthNumber(temproraryMonthNumber);
    }
    if (temproraryYearNumber !== yearNumber) {
      setYearNumber(temproraryYearNumber);
    }
  }

  const handleSetSelectedDate = (index) => {
    const selectedDateInfo = calendarData[index];
    const newSelectedDate = {
      day: selectedDateInfo.day,
      month: selectedDateInfo.month,
      year: selectedDateInfo.year
    };
    setSelectedDate(newSelectedDate);
    checkboxStore.setSelectedDate(newSelectedDate)
    if (tg.MainButton.isActive) {
      tg.MainButton.disable();
      tg.MainButton.setText("Далее")
      if (tg.colorScheme === "light") {
        tg.MainButton.color = "#E8E8E9";
        tg.MainButton.textColor = "#B9B9BA";
      } else {
        tg.MainButton.color = "#2F2F2F";
        tg.MainButton.textColor = "#606060";
      }
    }
  }



  return (
    <div>
      <div className={cl.container}>

        <div className={cl.monthYearContainer}>
          <HeadLineSemibold className={cl.monthText}>{monthNames[monthNumber]}</HeadLineSemibold>
          <HeadLineMonoNumbers className={cl.yearText}>{yearNumber}</HeadLineMonoNumbers>
        </div>
        <DayRadio calendarData={calendarData} scrollSetMonthName={scrollSetMonthName} handleSetSelectedDate={handleSetSelectedDate} selectedDate={selectedDate} />
      </div>
      <FreeTime selectedDate={selectedDate} />

    </div>
  )
})

export default Calendar;