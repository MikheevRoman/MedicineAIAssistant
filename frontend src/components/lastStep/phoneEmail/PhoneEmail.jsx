import cl from './PhoneEmail.module.css'
import { InputMask } from '@react-input/mask';
import { useState, useEffect } from 'react';
import { useCheckboxStore } from '../../../store/CheckboxStore';
import validationStore from '../../../store/ValidationStore';

const PhoneEmail = ({phoneNumber, setPhoneNumber, email, setEmail}) => {
    const checkboxStore = useCheckboxStore();
    

    const handlePhoneNumberChange = (e) => {
        setPhoneNumber(e.target.value);
    };

    const handlePhoneNumberFocus = (e) => {
        if (e.target.value === '') {
            e.target.value = '+7 (';
            setPhoneNumber('+7 ('); // Установите начальное значение при фокусировке
        }
    };

    useEffect(() => {
        const savedPhoneNumber = localStorage.getItem('phoneNumber');
        const savedEmail = localStorage.getItem('clientEmail');

        if (savedEmail) {
            setEmail(savedEmail);
            checkboxStore.clientEmail = email;
        }
        if (savedPhoneNumber) {
            setPhoneNumber(savedPhoneNumber);
            checkboxStore.setClientPhoneNumber(phoneNumber);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        localStorage.setItem('phoneNumber', phoneNumber);
        checkboxStore.setClientPhoneNumber(phoneNumber);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [phoneNumber]);

    useEffect(() => {
        localStorage.setItem('clientEmail', email);
        checkboxStore.clientEmail = email;
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [email]);

    return (
        <div className={cl.container}>

            <div className={cl.inputWrapper} style={{ borderTopLeftRadius: '10px', borderTopRightRadius: '10px' }}>
                <InputMask
                    mask="+7 (___) ___-__-__"
                    value={phoneNumber}
                    replacement={{ _: /\d/ }}
                    onChange={handlePhoneNumberChange}
                    onFocus={handlePhoneNumberFocus}
                    className={cl.inpt}
                    placeholder="Номер телефона"
                    style={{ borderTopLeftRadius: '10px', borderTopRightRadius: '10px' }}
                />
                <div className={cl.borderBottom}></div>
            </div>

            <div className={cl.inputWrapper} style={{ borderBottomLeftRadius: '10px', borderBottomRightRadius: '10px' }}>
                <input
                    type="text"
                    value={email}
                    onChange={(e) => validationStore.handleReguralInputChange(e, setEmail)}
                    placeholder="Почта"
                    className={cl.inpt}
                    style={{ borderBottomLeftRadius: '10px', borderBottomRightRadius: '10px' }}
                />
                <div className={cl.borderBottom}></div>
            </div>

        </div>
    )
}

export default PhoneEmail