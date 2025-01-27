import React from "react";
import { Swiper, SwiperSlide } from 'swiper/react';
import cl from "./Photos.module.css";
import { Pagination, Navigation } from 'swiper/modules';

import 'swiper/css';
import 'swiper/css/pagination';
import 'swiper/css/navigation';

const Photos = ({ photos }) => {
    
    const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    

    const base64ToImageUrl = (base64) => `data:image/jpeg;base64,${base64}`;

    return (
        <div className={cl.containerSwiper}>
            <Swiper
                slidesPerView={1}
                spaceBetween={30}
                loop={true}
                pagination={{
                    clickable: true,
                }}
                navigation={!isMobileDevice}
                modules={[Pagination, Navigation]}
                className={cl.mySwiper}
            >
                {photos.map((photoBase64, index) => (
                    <SwiperSlide key={index} className={cl.swiperSlide}>
                        <img src={base64ToImageUrl(photoBase64)} alt={`Фото ${index}`} className={cl.swiperSlideImg} />
                    </SwiperSlide>
                ))}
            </Swiper>
        </div>
    )
}

export default Photos