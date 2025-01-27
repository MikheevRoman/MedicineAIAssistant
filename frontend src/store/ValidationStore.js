import { makeObservable, action } from 'mobx';

class ValidationStore {
    maxRegularInputLength = 200;

    constructor() {
        makeObservable(this, {            
            handleReguralInputChange: action
        }, {deep: true, });
    }

    handleReguralInputChange = (e, setState) => {
        const value = e.target.value;
    
        // Если длина строки превышает максимальное количество символов, обрезаем её
        if (value.length > this.maxRegularInputLength) {
            setState(value.slice(0, this.maxRegularInputLength));
        } else {
            setState(value);
        }
    };
}

const validationStore = new ValidationStore();

export default validationStore;