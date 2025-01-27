import { useState, useEffect } from "react";
import cl from "./FreeTime.module.css"
import PeriodOfTime from "./periodOfTime/PeriodOfTime";
import { useCheckboxStore } from "../../../store/CheckboxStore";
import { HeadlineBody } from "../../../textStyles/TextStyleComponents";
import fetchStore from "../../../store/FetchStore";
import { observer } from "mobx-react-lite";

const FreeTime = observer(({ selectedDate }) => {
    const [freeMorningSlots, setFreeMorningSlots] = useState([]);
    const [freeDaySlots, setFreeDaySlots] = useState([]);
    const [freeEveningSlots, setFreeEveningSlots] = useState([]);

    const [selectedTime, setSelectedTime] = useState('');

    let tg = window.Telegram.WebApp;

    const checkboxStore = useCheckboxStore();

    const durationOfMedics = checkboxStore.totalSelectedTime;

    const intervalOfTime = 15;

    const currentDate = new Date();
    const currentDay = currentDate.getDate();
    const currentHours = currentDate.getHours();
    const currentMinutes = currentDate.getMinutes();

    function getTimeInMinutes(timeString) {
        const [hours, minutes] = timeString.split(":").map(Number);
        return hours * 60 + minutes;
    }

    const handleTimeSelection = (time) => {
        setSelectedTime(time);
        const endTimeInMinutes = getTimeInMinutes(time) + durationOfMedics

        const endHours = Math.floor(endTimeInMinutes / 60);
        const endMinutes = (endTimeInMinutes % 60).toString().padStart(2, '0');

        tg.MainButton.text = "Далее " + time + " - " + endHours + ":" + endMinutes;
        if (!tg.MainButton.isActive) {
            tg.MainButton.enable()
            tg.MainButton.color = tg.themeParams.button_color
            tg.MainButton.textColor = tg.themeParams.button_text_color
        }
        checkboxStore.setSelectedTime(time);
    };


    useEffect(() => {
        const formattedDate = `${selectedDate.year}-${String(selectedDate.month + 1).padStart(2, '0')}-${String(selectedDate.day).padStart(2, '0')}`;

        const selectedDateObj = new Date(selectedDate.year, selectedDate.month, selectedDate.day);

        // Проверяем, является ли выбранная дата меньше текущей
        if (selectedDateObj < currentDate.setHours(0, 0, 0, 0)) {
            setFreeMorningSlots([]);
            setFreeDaySlots([]);
            setFreeEveningSlots([]);
            return;
        }

        const dayData = fetchStore.workedDaysData.find(day => day.date === formattedDate);

        if (dayData && dayData.status === "WORK") {
            const freeSlots = dayData.recordingCells.filter(slot => slot.status === "FREE");

            const visibleSlots = [];
            const countOfNeededTime = Math.ceil(durationOfMedics / intervalOfTime);
            const freeSlotsInMinutes = freeSlots.map(slot => getTimeInMinutes(slot.time));

            freeSlots.forEach(slot => {
                const currentTimeInMinutes = getTimeInMinutes(slot.time);
                const arrayOfNeededSlotsForCurrentTime = [];
                for (let j = 0; j < countOfNeededTime; j++) {
                    arrayOfNeededSlotsForCurrentTime.push(currentTimeInMinutes + intervalOfTime * j);
                }

                const allExist = arrayOfNeededSlotsForCurrentTime.every(element => freeSlotsInMinutes.includes(element));
                if (allExist) {
                    visibleSlots.push(slot.time);
                }
            })

            if (selectedDate.day === currentDay) {
                const morningSlots = visibleSlots.filter(slot => {
                    const hours = parseInt(slot.split(":")[0]);
                    const minutes = parseInt(slot.split(":")[1]);
                    const currentTime = currentHours * 60 + currentMinutes;
                    const time = hours * 60 + minutes;
                    return hours < 12 && time >= currentTime;
                });

                const daySlots = visibleSlots.filter(slot => {
                    const hours = parseInt(slot.split(":")[0]);
                    const minutes = parseInt(slot.split(":")[1]);
                    const currentTime = currentHours * 60 + currentMinutes;
                    const time = hours * 60 + minutes;
                    return hours >= 12 && hours < 18 && time >= currentTime;
                });

                const eveningSlots = visibleSlots.filter(slot => {
                    const hours = parseInt(slot.split(":")[0]);
                    const minutes = parseInt(slot.split(":")[1]);
                    const currentTime = currentHours * 60 + currentMinutes;
                    const time = hours * 60 + minutes;
                    return hours >= 18 && time >= currentTime;
                });
                setFreeMorningSlots(morningSlots);
                setFreeDaySlots(daySlots);
                setFreeEveningSlots(eveningSlots);

            } else {

                const morningSlots = visibleSlots.filter(slot => {
                    const time = parseInt(slot.split(":")[0]);
                    return time < 12;
                });

                const daySlots = visibleSlots.filter(slot => {
                    const time = parseInt(slot.split(":")[0]);
                    return time >= 12 && time < 18;
                });

                const eveningSlots = visibleSlots.filter(slot => {
                    const time = parseInt(slot.split(":")[0]);
                    return time >= 18;
                });
                setFreeMorningSlots(morningSlots);
                setFreeDaySlots(daySlots);
                setFreeEveningSlots(eveningSlots);
            }


        } else {
            setFreeMorningSlots([]);
            setFreeDaySlots([]);
            setFreeEveningSlots([]);
        }
        setSelectedTime('');

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedDate, currentDay, currentHours, currentMinutes, durationOfMedics, fetchStore.fetchWorkedDaysData]);

    return (
        <div className={cl.container}>
            <PeriodOfTime freeSlots={freeMorningSlots} name={"morning"} onTimeSelect={handleTimeSelection} selectedDay={selectedDate.day} selectedMonth={selectedDate.month} selectedTime={selectedTime}>Утро</PeriodOfTime>
            <PeriodOfTime freeSlots={freeDaySlots} name={"day"} onTimeSelect={handleTimeSelection} selectedDay={selectedDate.day} selectedMonth={selectedDate.month} selectedTime={selectedTime}>День</PeriodOfTime>
            <PeriodOfTime freeSlots={freeEveningSlots} name={"evening"} onTimeSelect={handleTimeSelection} selectedDay={selectedDate.day} selectedMonth={selectedDate.month} selectedTime={selectedTime}>Вечер</PeriodOfTime>



            {freeMorningSlots.length === 0 && freeDaySlots.length === 0 && freeEveningSlots.length === 0 && (
                <div className={cl.busyDayContainer}>
                    <HeadlineBody className={cl.busyDay}>
                        На данный день
                    </HeadlineBody>

                    <HeadlineBody className={cl.busyDay}>
                        нет свободных окошек
                    </HeadlineBody>
                </div>
            )}
        </div>
    )
})

export default FreeTime