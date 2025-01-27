import React from "react";
import cl from "./MedicDatePlace.module.css";
import { HeadlineBody, HeadLineSemibold } from "../../../textStyles/TextStyleComponents";
import { useCheckboxStore } from "../../../store/CheckboxStore";
import fetchStore from "../../../store/FetchStore";
import { useState } from "react";

const MedicDatePlace = () => {
    const checkboxStore = useCheckboxStore();


    const selectedMedics = Object.keys(fetchStore.medicsData).reduce((result, category) => {
        if (result) return result; // Если уже нашли, выходим
        return fetchStore.medicsData[category].find(medic => medic.id === checkboxStore.doctor)?.name || null;
    }, null);

    const selectedInstitution = fetchStore.institutionData.find(institution => institution.id === checkboxStore.inistitution)?.name || null;

    function getTimeInMinutes(timeString) {
        const [hours, minutes] = timeString.split(":").map(Number);
        return hours * 60 + minutes;
    }

    function formatDate(day, monthIndex, time) {
        const months = [
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
        ];
        const monthName = months[monthIndex];
        return `${day} ${monthName}, ${time}`;
    }

    function formatEndTime(time, duration) {
        const timeInMinute = getTimeInMinutes(time);
        const endTimeInMinute = timeInMinute + duration;
        const endHours = Math.floor(endTimeInMinute / 60);
        const endMinutes = (endTimeInMinute % 60).toString().padStart(2, '0');
        return `- ${endHours}:${endMinutes}`;
    }

    const day = checkboxStore.selectedDate.day;
    const monthIndex = checkboxStore.selectedDate.month;
    const time = checkboxStore.selectedTime;
    const duration = checkboxStore.totalSelectedTime;

    const dateString = formatDate(day, monthIndex, time);
    const endTime = formatEndTime(time, duration);

    return (
        <div className={cl.container}>

            <div className={cl.inscriptionContainer}>
                <HeadLineSemibold>Врач:</HeadLineSemibold>
                <HeadlineBody>{`${checkboxStore.doctorName} (${checkboxStore.doctorCategory})`}</HeadlineBody>
            </div>


            <div className={cl.inscriptionContainer}>
                <HeadLineSemibold>Дата:</HeadLineSemibold>
                <HeadlineBody>{dateString}</HeadlineBody>
                <HeadlineBody className={cl.hintText}>{endTime}</HeadlineBody>
            </div>

            <div className={cl.inscriptionContainer}>
                <HeadLineSemibold>Место:</HeadLineSemibold>
                <HeadlineBody className={cl.hintText}>{checkboxStore.institutionName}</HeadlineBody>
            </div>

            <div className={cl.inscriptionContainer}>
                <HeadLineSemibold>Цена:</HeadLineSemibold>
                <HeadlineBody>{`${checkboxStore.totalSelectedPrice} ₽`}</HeadlineBody>
            </div>
        </div>
    );
};

export default MedicDatePlace;
