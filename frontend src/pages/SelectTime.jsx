import React from "react";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import MedicsHeader from "../components/header/MedicsHeader";
import Calendar from "../components/selectTime/calendar/Calendar";
import { useCheckboxStore } from "../store/CheckboxStore";
import fetchStore from "../store/FetchStore";

const SelectTime = () => {
  const tg = window.Telegram.WebApp;
  const navigate = useNavigate();

  const checkboxStore = useCheckboxStore();

  useEffect(() => {
    if (Object.keys(fetchStore.medicsData).length === 0) {
      navigate('*')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function getTimeInMinutes(timeString) {
    const [hours, minutes] = timeString.split(":").map(Number);
    return hours * 60 + minutes;
  }

  useEffect(() => {
    const handleMainButtonOnClick = () => {
      navigate("/lastStep");
    }

    const handleBackButtonOnClick = () => {
      navigate("/medics");
    }

    tg.MainButton.onClick(handleMainButtonOnClick);

    tg.BackButton.onClick(handleBackButtonOnClick);

    tg.BackButton.show();

    if (checkboxStore.selectedTime == null) {
      if (tg.MainButton.isActive) {
        tg.MainButton.disable();
        tg.MainButton.setText("Далее")
        if (tg.colorScheme === "light") {
          tg.MainButton.color = "#e8e8e9";
          tg.MainButton.textColor = "#b9b9ba";
        } else {
          tg.MainButton.color = "#2f2f2f";
          tg.MainButton.textColor = "#606060";
        }
      }
    } else {
      if (!tg.MainButton.isActive) {
        tg.MainButton.enable()
      }
      if (tg.MainButton.color !== tg.themeParams.button_color) {
        tg.MainButton.color = tg.themeParams.button_color
        tg.MainButton.textColor = tg.themeParams.button_text_color
      }

      const endTimeInMinutes = getTimeInMinutes(checkboxStore.selectedTime) + checkboxStore.totalSelectedTime
      const endHours = Math.floor(endTimeInMinutes / 60);
      const endMinutes = (endTimeInMinutes % 60).toString().padStart(2, '0');
      tg.MainButton.text = "Далее " + checkboxStore.selectedTime + " - " + endHours + ":" + endMinutes;
    }

    return () => {
      tg.MainButton.offClick(handleMainButtonOnClick);
      tg.BackButton.offClick(handleBackButtonOnClick);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (

    <div>
      <MedicsHeader>Выберите время</MedicsHeader>
      <Calendar />
    </div>
  )
}

export default SelectTime;