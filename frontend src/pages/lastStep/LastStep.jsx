import { useNavigate } from "react-router-dom";
import MedicsHeader from "../../components/header/MedicsHeader";
import { useEffect, useState } from "react";
import DualInputDropdown from "../../components/lastStep/dualInputDropdown/dualInputDropdown/DualInputDropdown";

import cl from "./LastStep.module.css"
import MedicDatePlace from "../../components/lastStep/medicDatePlace/MedicDatePlace";
import { useCheckboxStore } from "../../store/CheckboxStore";
import axios from "axios";
import { observer } from "mobx-react-lite";
import fetchStore from "../../store/FetchStore";
import ModalUniversal from '../../components/universalComponents/modalUniversal/ModalUniversal'
import PhoneEmail from "../../components/lastStep/phoneEmail/PhoneEmail";
import Remind from "../../components/lastStep/remind/Remind";

const LastStep = observer(() => {
  let tg = window.Telegram.WebApp;
  const navigate = useNavigate();

  const checkboxStore = useCheckboxStore()

  const [showErrorModal, setShowErrorModal] = useState(false);


  const [nameOfClient, setNameOfClient] = useState('');
  const [surnameOfClient, setSurnameOfClient] = useState('');
  const [patronymicOfClient, setPatronymicOfClient] = useState('');
  const [birthdayOfClient, setBirthdayOfClient] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');


  useEffect(() => {
    if (Object.keys(fetchStore.medicsData).length === 0) {
      navigate('*')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (Object.keys(fetchStore.medicsData).length === 0) {
    return null;
  }

  const botUsername = localStorage.getItem('botUsername')

  const localDateTimeString = `${checkboxStore.selectedDate.year}-${(checkboxStore.selectedDate.month + 1).toString().padStart(2, '0')}-${checkboxStore.selectedDate.day.toString().padStart(2, '0')}T${checkboxStore.selectedTime}:00`;

  const localDate = new Date(localDateTimeString);

  const dateInUTC = localDate.toISOString();

  const date = `${checkboxStore.selectedDate.year}-${(checkboxStore.selectedDate.month + 1).toString().padStart(2, '0')}-${checkboxStore.selectedDate.day.toString().padStart(2, '0')} ${checkboxStore.selectedTime}`;

  // let dateInUTCForRemind;
  // if (checkboxStore.clientRemindMinutes !== 0) {
  //   const newUtcDate = new Date(dateInUTC);
  //   newUtcDate.setMinutes(newUtcDate.getMinutes() - checkboxStore.clientRemindMinutes);
  //   dateInUTCForRemind = newUtcDate.toISOString();
  // } else {
  //   dateInUTCForRemind = null;
  // }



  useEffect(() => {
    const handleBackButtonOnClick = () => {
      navigate("/selectTime");
    }

    const handleMainButtonOnClick = async () => {
      tg.MainButton.disable();

      const requestData = {
        userId: localStorage.getItem('actorUserId'),
        time: date,
        institutionName: checkboxStore.institutionName,
        institutionAddress: checkboxStore.institutionAddress,
        specialist: checkboxStore.doctorName,
        specialisation: checkboxStore.doctorCategory
      };

      try {
        const response = await axios.post(`https://medicine-telegram-bot.gros.pro/bot/new-appointment`, requestData);
        console.log('Ответ от сервера:', response.data);

        tg.close();
      } catch (error) {
        setShowErrorModal(true);
        tg.MainButton.enable();
        console.log(error)
        if (error.response) {
          // Сервер вернул ответ с кодом ошибки, который находится в пределах диапазона 2xx
          const errorData = error.response.data;
          console.error("Ошибка:", errorData.error);
          console.error("Описание:", errorData.description);
        } else if (error.request) {
          // Запрос был сделан, но ответа не было получено
          console.error("Запрос был сделан, но ответа не было получено", error.request);
        } else {
          // Произошла другая ошибка при настройке запроса
          console.error("Ошибка:", error.message);
        }
      }
    }

    tg.BackButton.onClick(handleBackButtonOnClick);

    tg.MainButton.disable();

    if (tg.colorScheme === "light") {
      tg.MainButton.color = "#e8e8e9";
      tg.MainButton.textColor = "#b9b9ba";
    } else {
      tg.MainButton.color = "#2f2f2f";
      tg.MainButton.textColor = "#606060";
    }

    tg.MainButton.setText("Записаться");

    tg.MainButton.onClick(handleMainButtonOnClick)

    return () => {
      tg.BackButton.offClick(handleBackButtonOnClick);
      tg.MainButton.offClick(handleMainButtonOnClick);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const isPhoneNumberComplete = phoneNumber.length === 18;

    const isBirthdayComplete = birthdayOfClient.length === 10;

    if (nameOfClient.trim() && surnameOfClient.trim() && isBirthdayComplete && isPhoneNumberComplete && email.trim()) {
      tg.MainButton.color = "#34C759";
      tg.MainButton.textColor = "#FFFFFF";
      tg.MainButton.enable();
    } else {
      tg.MainButton.disable();
      if (tg.colorScheme === "light") {
        tg.MainButton.color = "#e8e8e9";
        tg.MainButton.textColor = "#b9b9ba";
      } else {
        tg.MainButton.color = "#2f2f2f";
        tg.MainButton.textColor = "#606060";
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nameOfClient, phoneNumber, surnameOfClient, birthdayOfClient, email]);

  return (
    <div>
      <MedicsHeader>Последний шаг</MedicsHeader>
      <DualInputDropdown nameOfClient={nameOfClient} setNameOfClient={setNameOfClient} surnameOfClient={surnameOfClient} setSurnameOfClient={setSurnameOfClient} patronymicOfClient={patronymicOfClient} setPatronymicOfClient={setPatronymicOfClient} birthdayOfClient={birthdayOfClient} setBirthdayOfClient={setBirthdayOfClient} />

      <PhoneEmail phoneNumber={phoneNumber} setPhoneNumber={setPhoneNumber} email={email} setEmail={setEmail} />

      <Remind />

      <MedicDatePlace />

      {showErrorModal &&
        <ModalUniversal
          text={'Не удалось записаться.\nПопробуйте снова'}
          setIsVisible={setShowErrorModal}
          cancelText={'Окей'}
        />
      }

    </div>
  )
})

export default LastStep