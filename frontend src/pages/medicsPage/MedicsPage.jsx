import { observer } from "mobx-react-lite";
import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { HeadlineBody } from "../../textStyles/TextStyleComponents";
import MedicsHeader from "../../components/header/MedicsHeader";
import MedicsBlocks from "../../components/medics/blocks/MedicsBlocks";
import { useCheckboxStore } from "../../store/CheckboxStore";
import fetchStore from "../../store/FetchStore";
import cl from './MedicsPage.module.css';

const Medics = observer(() => {
    const tg = window.Telegram.WebApp;

    const checkboxStore = useCheckboxStore();

    const navigate = useNavigate()

    useEffect(() => {
        if (Object.keys(fetchStore.medicsData).length === 0) {
            navigate('*')
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    useEffect(() => {
        const handleMainButtonOnClick = () => {
            navigate("/selectTime");
        }

        const handleBackButtonOnClick = () => {
            navigate("*");
        }

        tg.MainButton.onClick(handleMainButtonOnClick);
        tg.BackButton.onClick(handleBackButtonOnClick);

        tg.BackButton.show();

        if (!tg.MainButton.isActive) {
            tg.MainButton.enable()
            tg.MainButton.color = tg.themeParams.button_color
            tg.MainButton.textColor = tg.themeParams.button_text_color

        }

        if (checkboxStore.doctorName && !tg.MainButton.isVisible) {
            tg.MainButton.show();
        }

        if (!checkboxStore.doctorName && tg.MainButton.isVisible) {
            tg.MainButton.hide();
        }

        return () => {
            tg.MainButton.offClick(handleMainButtonOnClick);
            tg.BackButton.offClick(handleBackButtonOnClick);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])



    return (
        <div>
            {Object.keys(fetchStore.medicsData).length !== 0
                ? <div>
                    <MedicsHeader>Выберите врача</MedicsHeader>
                    <MedicsBlocks isInstitution={true} medicsEntries={fetchStore.institutionData} />
                </div>

                : <div className={cl.noMedicsContainer}>
                    <HeadlineBody className={cl.noMedicsText}> Владелец пока не добавил врача </HeadlineBody>
                </div>
            }
        </div>
    )
})

export default Medics;