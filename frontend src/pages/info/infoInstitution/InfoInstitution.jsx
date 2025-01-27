import { useNavigate, useParams } from 'react-router-dom';
import MedicsHeader from '../../../components/header/MedicsHeader';
import Photos from '../../../components/info/Photos';
import { HeadlineBody } from '../../../textStyles/TextStyleComponents';
import cl from './InfoInstitution.module.css'
import { useEffect, useState } from 'react';
import fetchStore from '../../../store/FetchStore';

const InfoInstitution = () => {
    let tg = window.Telegram.WebApp;
    const navigate = useNavigate();
    const { id } = useParams();



    // const [itemId, setItemId] = useState('');
    const [itemInfo, setItemInfo] = useState({
        name: '',
        photos: [],
        address: '',
        description: ''
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
            navigate("*");
        }

        tg.BackButton.onClick(handleBackButtonOnClick);

        return () => {
            tg.BackButton.offClick(handleBackButtonOnClick)
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        const getItemById = () => {
            const selectedItem = { name: '', photos: [], address: '', description: '' };

            // Итерация по массиву объектов и поиск элемента по ID
            const foundItem = fetchStore.institutionData.find(item => String(item.id) === id);

            if (foundItem) {
                return {
                    name: foundItem.name,
                    photos: Array.isArray(foundItem.photos) ? foundItem.photos : [],
                    address: foundItem.address,
                    description: foundItem.description
                };
            }

            return selectedItem;
        };

        setItemInfo(getItemById());
    }, [id]);



    const moment = require('moment');



    return (
        <div>
            <div>
                {itemInfo.photos.length > 0 && (
                    <Photos photos={itemInfo.photos} />

                )}

                <MedicsHeader>{itemInfo.name}</MedicsHeader>

                <HeadlineBody className={cl.address}>Адрес: {itemInfo.address} </HeadlineBody>

                <HeadlineBody className={cl.description}>{itemInfo.description}</HeadlineBody>
            </div>
        </div>
    )
}

export default InfoInstitution