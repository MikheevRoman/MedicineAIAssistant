import { useState, useEffect, useRef } from "react";
import cl from "./DualInputDropdown.module.css"
import { InputMask } from '@react-input/mask';
import validationStore from "../../../../store/ValidationStore";
import { ReactComponent as SelectRemindIcon } from "../../../../vectorIcons/SelectRemindIcon.svg"
import { HeadlineBody } from "../../../../textStyles/TextStyleComponents";
import { useCheckboxStore } from "../../../../store/CheckboxStore";



const DualInputDropdown = ({nameOfClient, setNameOfClient, surnameOfClient, setSurnameOfClient, patronymicOfClient, setPatronymicOfClient, birthdayOfClient, setBirthdayOfClient}) => {
    const tg = window.Telegram.WebApp;

    const checkboxStore = useCheckboxStore();

    

    useEffect(() => {
        const savedName = localStorage.getItem('nameOfClient');
        const savedSurname = localStorage.getItem('surnameOfClient');
        const savedPatronymic = localStorage.getItem('patronymicOfClient');
        const savedBirthday = localStorage.getItem('birthdayOfClient');


        if (savedName) {
            setNameOfClient(savedName);
            checkboxStore.setClientName(nameOfClient);
        }
        if (savedSurname) {
            setSurnameOfClient(savedName);
            checkboxStore.clientSurname = surnameOfClient;
        }
        if (savedName) {
            setPatronymicOfClient(savedPatronymic);
            checkboxStore.clientPatronymic = patronymicOfClient;
        }
        if (savedBirthday) {
            setBirthdayOfClient(savedBirthday);
            checkboxStore.clientBirthday = birthdayOfClient;
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        localStorage.setItem('nameOfClient', nameOfClient);
        checkboxStore.setClientName(nameOfClient);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [nameOfClient]);

    useEffect(() => {
        localStorage.setItem('surnameOfClient', surnameOfClient);
        checkboxStore.clientSurname = surnameOfClient;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [surnameOfClient]);

    useEffect(() => {
        localStorage.setItem('patronymicOfClient', patronymicOfClient);
        checkboxStore.clientPatronymic = patronymicOfClient;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [patronymicOfClient]);

    useEffect(() => {
        localStorage.setItem('birthdayOfClient', birthdayOfClient);
        checkboxStore.clientBirthday = birthdayOfClient;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [birthdayOfClient]);



    return (
        <div className={cl.container}>
            <div className={cl.inputWrapper} style={{ borderTopLeftRadius: '10px', borderTopRightRadius: '10px' }}>
                <input
                    type="text"
                    value={nameOfClient}
                    onChange={(e) => validationStore.handleReguralInputChange(e, setNameOfClient)}
                    placeholder="Имя"
                    className={cl.inpt}
                    style={{ borderTopLeftRadius: '10px', borderTopRightRadius: '10px' }}
                />
                <div className={cl.borderBottom}></div>
            </div>

            <div className={cl.inputWrapper} >
                <input
                    type="text"
                    value={surnameOfClient}
                    onChange={(e) => validationStore.handleReguralInputChange(e, setSurnameOfClient)}
                    placeholder="Фамилия"
                    className={cl.inpt}
                />
                <div className={cl.borderBottom}></div>
            </div>

            <div className={cl.inputWrapper} >
                <input
                    type="text"
                    value={patronymicOfClient}
                    onChange={(e) => validationStore.handleReguralInputChange(e, setPatronymicOfClient)}
                    placeholder="Отчество"
                    className={cl.inpt}
                />
                <div className={cl.borderBottom}></div>
            </div>

            <div className={cl.inputWrapper} style={{ borderBottomLeftRadius: '10px', borderBottomRightRadius: '10px' }}>
                <InputMask
                    mask="dd.dd.dddd"
                    replacement={{ d: /\d/ }}
                    value={birthdayOfClient}
                    onChange={(e) => validationStore.handleReguralInputChange(e, setBirthdayOfClient)}
                    placeholder="Дата рождения"
                    className={cl.inpt}
                    style={{ borderBottomLeftRadius: '10px', borderBottomRightRadius: '10px' }}
                    onBlur={() => {
                        if (!/^\d{2}\.\d{2}\.\d{4}$/.test(birthdayOfClient)) {
                            setBirthdayOfClient('');
                        }
                    }}
                />
                <div className={cl.borderBottom}></div>
            </div>

        </div>
    )
}

export default DualInputDropdown
