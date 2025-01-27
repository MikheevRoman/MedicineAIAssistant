import cl from './MedicalOrganization.module.css'
import fetchStore from '../../store/FetchStore';
import { useEffect } from 'react';
import { useCheckboxStore } from '../../store/CheckboxStore';
import { HeadlineBody } from '../../textStyles/TextStyleComponents';
import MedicsBlocks from '../../components/medics/blocks/MedicsBlocks';
import MedicsHeader from "../../components/header/MedicsHeader";
import { useNavigate } from 'react-router-dom';

const MedicalOrganization = () => {
    const tg = window.Telegram.WebApp;
    const navigate = useNavigate()


    const checkboxStore = useCheckboxStore();

    const params = new URLSearchParams(window.location.search); // добавил вместо с улосвием в инит дате

    useEffect(() => {
        const initData = tg.initData;

        if (initData) {

            const parseInitData = (initData) => {
                return Object.fromEntries(new URLSearchParams(initData));
            };

            const parsedData = parseInitData(initData);

            localStorage.setItem('actorUserId', JSON.parse(parsedData.user).id);
        } else {
            localStorage.setItem('actorUserId', params.get('clientUserId'))
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    useEffect(() => {
        // const params = new URLSearchParams(window.location.search); // закомментил
        const botUsername = params.get('botUsername');
        const actor = params.get('actor');
        const clientUserId = params.get('clientUserId');

        // если мастер записывает клиента, тогда в качестве идентификатора для запросов на сервер, отправляем userId мастера
        if (botUsername === 'GrosMedicBot') {
            localStorage.setItem('botUsername', localStorage.getItem('actorUserId')); // actorUserId по факту является userId мастера
            localStorage.setItem('clientUserId', clientUserId);

        } else {
            if (botUsername) {
                localStorage.setItem('botUsername', botUsername);
                localStorage.setItem('clientUserId', localStorage.getItem('actorUserId'));
            }
        }

        if (actor) {
            localStorage.setItem('actor', actor);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);



    useEffect(() => {
        const handleMainButtonOnClick = () => {
            navigate("/medics");
        }

        tg.MainButton.onClick(handleMainButtonOnClick);

        tg.BackButton.hide();

        tg.MainButton.text = "Далее";

        if (!tg.MainButton.isActive) {
            tg.MainButton.enable()
            tg.MainButton.color = tg.themeParams.button_color
            tg.MainButton.textColor = tg.themeParams.button_text_color
        }
        if (checkboxStore.institutionName && !tg.MainButton.isVisible) {
            tg.MainButton.show();
        }
        if (!checkboxStore.institutionName && tg.MainButton.isVisible) {
            tg.MainButton.hide();
        }

        return () => {
            tg.MainButton.offClick(handleMainButtonOnClick);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])


    return (
        <div>
            {fetchStore.institutionData.length !== 0
                ? <div>
                    <MedicsHeader>Выберите медорганизацию</MedicsHeader>
                    <MedicsBlocks />
                </div>

                : <div className={cl.noMedicsContainer}>
                    <HeadlineBody className={cl.noMedicsText}> Владелец пока не добавил медорганизацию </HeadlineBody>
                </div>
            }
        </div>
    )
}

export default MedicalOrganization