import React from "react";
import { HeadlineBody } from "../../textStyles/TextStyleComponents";
import MedicsHeader from "../../components/header/MedicsHeader";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import cl from "./Info.module.css"
import Photos from "../../components/info/Photos";
import { observer } from "mobx-react-lite";
import fetchStore from "../../store/FetchStore";


const Info = observer(() => {



  // const [currentIndex, setCurrentIndex] = useState(0);

  // const showNextImage = () => {
  //   const nextIndex = (currentIndex + 1) % images.length;
  //   setCurrentIndex(nextIndex);
  // };


  let tg = window.Telegram.WebApp;
  const navigate = useNavigate();
  const { id } = useParams();

  // const [itemId, setItemId] = useState('');
  const [itemInfo, setItemInfo] = useState({
    name: '',
    photos: [],
    time: '',
    info: ''
  });

  useEffect(() => {
    if (Object.keys(fetchStore.medicsData).length === 0) {
      navigate('*')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])


  useEffect(() => {
    tg.BackButton.show();

    const handleBackButtonOnClick = () => {
      navigate("/medics");
    }

    tg.BackButton.onClick(handleBackButtonOnClick);

    return () => {
      tg.BackButton.offClick(handleBackButtonOnClick)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const getItemById = () => {
      let selectedItem = { name: '', photos: [], time: '', description: '' };

      // Итерация по категориям услуг и поиск услуги по ID
      Object.values(fetchStore.medicsData).forEach(categoryItems => {
        const foundItem = categoryItems.find(item => String(item.id) === id);
        if (foundItem) {
          selectedItem = {
            name: foundItem.name,
            photos: Array.isArray(foundItem.photos) ? foundItem.photos : [],
            time: foundItem.duration,
            description: foundItem.description
          };
        }
      });
      return selectedItem;
    };
    setItemInfo(getItemById());
  }, [id]);


  const moment = require('moment');

  function formatMinutesToTimeString(minutes) {
    const duration = moment.duration(minutes, 'minutes');
    const hours = duration.hours();
    const mins = duration.minutes();

    let result = '';
    if (hours > 0) {
      result += hours + ' час';
      if (hours > 1) result += 'а';
      result += ' ';
    }
    if (mins > 0) {
      result += mins + ' минут';
    }
    return result;
  }

  return (
    <div>
      {itemInfo.photos.length > 0 && (
        <Photos photos={itemInfo.photos} />
      )}

      <MedicsHeader>{itemInfo.name}</MedicsHeader>

      <HeadlineBody className={cl.time}>Длительность: {formatMinutesToTimeString(itemInfo.time)} </HeadlineBody>

      <HeadlineBody className={cl.description}>{itemInfo.description}</HeadlineBody>
    </div>
  )
})

export default Info;