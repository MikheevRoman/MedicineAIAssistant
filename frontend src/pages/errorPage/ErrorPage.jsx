import { Title1, Title2 } from '../../textStyles/TextStyleComponents';
import cl from './ErrorPage.module.css';
import { useLocation, useNavigate } from "react-router-dom";
import { useEffect } from 'react';

const ErrorPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { errorCode, errorMessage } = location.state || {};
    const tg = window.Telegram.WebApp;


    const emoji = [`¯⁠\\⁠_⁠(×_×)⁠_⁠/⁠¯`, `(×_×)`, `ಠ⁠_⁠ಠ`];
    const randomIndex = Math.floor(Math.random() * emoji.length);

    useEffect(() => {
        tg.MainButton.text = "Ок";

        if (!tg.MainButton.isVisible) {
            tg.MainButton.show();
        }

        const handleMainButtonOnClick = () => {
            navigate('*');
        }

        tg.MainButton.onClick(handleMainButtonOnClick);

        return () => {
            tg.MainButton.offClick(handleMainButtonOnClick);
        };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className={cl.container}>
            <Title1>{errorCode}</Title1>
            <Title2>{errorMessage}</Title2>
            <Title2 className={cl.hintText}>
                {emoji[randomIndex]}
            </Title2>
        </div>
    );
};

export default ErrorPage