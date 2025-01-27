import cl from './ModalUniversal.module.css'
import { useEffect } from 'react';
import { HeadlineBody, HeadLineSemibold } from '../../../textStyles/TextStyleComponents';

const ModalUniversal = ({
    text,
    setIsVisible,
    onConfirm,
    confirmText,
    cancelText
}) => {
    const tg = window.Telegram.WebApp;

    const backdropClass = tg.colorScheme === 'dark' ? `${cl.backdrop} ${cl.dark}` : `${cl.backdrop} ${cl.light}`;
    const confirmButtonClass = confirmText === 'Удалить' || 'Уйти' 
    ? `${cl.button} ${cl.dualButton} ${cl.confirmDeleteButton}` 
    : `${cl.button} ${cl.dualButton} ${cl.confirmCancelButton}`;

    const buttonStyleClass = tg.colorScheme === 'dark' ? cl.darkButton : cl.lightButton;

    const onCancel = (event) => {
        event.stopPropagation();
        setIsVisible(false);
    }

    const handleBackdropClick = (event) => {
        if (event.currentTarget === event.target) {
            event.stopPropagation();
            setIsVisible(false);
        }
    };

    useEffect(() => {
        // При монтировании компонента
        document.body.style.overflow = 'hidden';

        // При демонтировании компонента
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, []);

    return (
        <div className={backdropClass} onClick={handleBackdropClick}>
            <div className={cl.container}>
                <div className={cl.textContainer}>
                    <HeadLineSemibold style={{ textAlign: "center", whiteSpace: 'pre-line' }}>{text}</HeadLineSemibold>
                </div>

                <div className={cl.buttonContainer}>
                    {onConfirm ?
                        <div className={cl.doubleButtonContainer}>
                            <div className={`${confirmButtonClass} ${buttonStyleClass} ${cl.borderBottomLeftRadius}`} onClick={onConfirm}><HeadLineSemibold>{confirmText}</HeadLineSemibold></div>
                            <div className={cl.border} />
                            <div className={`${cl.button} ${cl.confirmCancelButton} ${cl.dualButton} ${buttonStyleClass} ${cl.borderBottomRightRadius}`} onClick={onCancel}><HeadlineBody>{cancelText}</HeadlineBody></div>
                        </div>
                        :
                        <div className={`${cl.button} ${cl.singleButton} ${cl.confirmCancelButton} ${buttonStyleClass}`} onClick={onCancel}>
                            <HeadlineBody>
                                {cancelText}
                            </HeadlineBody>
                        </div>
                    }
                </div>
            </div>
        </div>
    )
}

export default ModalUniversal