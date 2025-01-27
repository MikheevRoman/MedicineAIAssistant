import { useCheckboxStore } from '../../../store/CheckboxStore';
import cl from './Remind.module.css'
import { useState, useRef, useEffect } from 'react';
import { ReactComponent as SelectRemindIcon } from "../../../vectorIcons/SelectRemindIcon.svg"
import { HeadlineBody } from '../../../textStyles/TextStyleComponents';

const options = [
    { value: 0, label: "Не напоминать" },
    { value: 15, label: "Напомнить за 15 минут" },
    { value: 30, label: "Напомнить за 30 минут" },
    { value: 60, label: "Напомнить за 1 час" },
    { value: 120, label: "Напомнить за 2 часа" },
    { value: 360, label: "Напомнить за 6 часов" },
    { value: 1440, label: "Напомнить за 1 сутки" },
];

const Remind = () => {
    const tg = window.Telegram.WebApp;
    const checkboxStore = useCheckboxStore();

    const [selectRemindIsVisible, setSelectRemindIsVisible] = useState(false);

    const dropdownRef = useRef(null);

    const dropdownBorderStyleClass = tg.colorScheme === 'dark' ? cl.darkBorderDropdown : cl.lightBorderDropdown;
    const dropdownItemStyleClass = tg.colorScheme === 'dark' ? cl.darkDropdownItem : cl.lightDropdownItem;

    const [selectedOption, setSelectedOption] = useState(() => {
        const savedOption = localStorage.getItem('selectedOption');
        checkboxStore.setClientRemindMinutes(localStorage.getItem('selectedOption'))
        return savedOption ? JSON.parse(savedOption) : { value: 0, label: "Не напоминать" };
    });

    useEffect(() => {
        localStorage.setItem('selectedOption', JSON.stringify(selectedOption));
        checkboxStore.setClientRemindMinutes(selectedOption.value)
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedOption]);

    const toggleRemindDropdown = () => {
        if (!selectRemindIsVisible) {
            setSelectRemindIsVisible(true);
        } else {
            setSelectRemindIsVisible(false);
        }
    }

    const handleRemindSelect = (option) => {
        setSelectedOption(option);
        setSelectRemindIsVisible(false);
    }

    const handleClickOutside = (event) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target) && !event.target.closest(`.${cl.selectContainer}`)) {
            setSelectRemindIsVisible(false);
        }
    };

    useEffect(() => {
        if (selectRemindIsVisible) {
            document.addEventListener('mousedown', handleClickOutside);
        } else {
            document.removeEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [selectRemindIsVisible]);

    return (
        <div className={cl.container}>
            <div className={cl.selectContainer} onClick={toggleRemindDropdown}>
                <HeadlineBody>{selectedOption.label}</HeadlineBody>
                <SelectRemindIcon />                
            </div>

            {selectRemindIsVisible &&
                <div ref={dropdownRef} className={`${cl.dropdownContainer} ${dropdownBorderStyleClass}`}>
                    {options.map((option, index) => (
                        <div
                            key={index}
                            className={`${cl.dropdownItem} ${dropdownItemStyleClass}
                            ${index === 0 && cl.firstDropdownItem}
                            ${index === options.length - 1 && cl.lastDropdownItem}
                            ${option.value === selectedOption.value && cl.linkText}
                            `}
                            onClick={() => handleRemindSelect(option)}
                        >
                            <HeadlineBody>{option.label}</HeadlineBody>
                            {index !== options.length - 1 && <div className={cl.borderBottom}></div>}
                        </div>
                    ))}
                </div>
            }
        </div>
    )
}

export default Remind