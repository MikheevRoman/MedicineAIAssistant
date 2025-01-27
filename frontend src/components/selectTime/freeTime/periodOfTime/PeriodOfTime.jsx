import { Footnote, HeadlineBody } from "../../../../textStyles/TextStyleComponents";
import cl from "./PeriodOfTime.module.css";
import { useCheckboxStore } from "../../../../store/CheckboxStore";

const PeriodOfTime = ({ children, freeSlots, name, onTimeSelect, selectedTime }) => {
    const checkboxStore = useCheckboxStore();
    return (
        freeSlots.length > 0 && (
            <div className={cl.container}>
                <Footnote className={cl.partOfDay}>{children}</Footnote>
                <div className={cl.freeTimeContainer}>
                    {freeSlots.map((slot, index) => (
                        <div key={index} className={cl.timeSlot}>
                            <input
                                type="radio"
                                id={`${name}-${index}`}
                                name="selectTime"
                                className={cl.radioInput}
                                value={slot}
                                onChange={() => onTimeSelect(slot)}
                                checked={checkboxStore.selectedTime === slot}
                            />
                            <label htmlFor={`${name}-${index}`} className={cl.timeLabel}>
                                <HeadlineBody>{slot}</HeadlineBody>
                            </label>
                        </div>
                    ))}
                </div>
            </div>
        )
    );
};

export default PeriodOfTime;