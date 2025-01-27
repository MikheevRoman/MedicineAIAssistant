import { observable, action, makeObservable } from 'mobx';
import { createContext, useContext } from 'react';

class CheckboxStore {
  inistitution = -1;
  doctor = -1;
  totalSelectedTime = 0;
  totalSelectedPrice = 0;
  selectedDate = null;
  
  selectedTime = null;

  doctorName = '';
  doctorCategory = '';
  institutionName = '';
  institutionAddress = '';
  
  clientName = '';
  clientSurname = '';
  clientPatronymic = '';
  clientBirthday = '';
  clientPhoneNumber = '';
  clientEmail = '';
  clientRemindMinutes = 0;
  // lastSelectedDate = null;

  constructor() {
    makeObservable(this, {
      inistitution: observable,
      doctor: observable,
      totalSelectedTime: observable,
      totalSelectedPrice: observable,
      selectedDate: observable,
      selectedTime: observable,

      clientName: observable,
      clientSurname: observable,
      clientPatronymic: observable,
      clientBirthday: observable,
      clientEmail: observable,
      clientPhoneNumber: observable,
      clientRemindMinutes: observable,

      institutionName: observable,
      institutionAddress: observable,
      doctorCategory: observable,
      doctorName: observable,
      // lastSelectedDate: observable,
      
      // getCheckedCheckboxIds: action,
      setSelectedDate: action,
      setSelectedTime: action,
      clearSelectedTime: action,
      setClientName: action,
      setClientPhoneNumber: action,      
      setClientRemindMinutes: action
      // setLastSelectedDate: action
    }, { deep: true, });
  }

  isCheckboxChecked(id) {
    return id === this.ch;
  }

  // getCheckedCheckboxIds() {
  //   return Array.from(this.checkboxes); // Возвращаем массив выбранных ID
  // }

  setSelectedDate(date) {
    this.selectedDate = date;
    this.selectedTime = null;
  }

  setSelectedTime(time) {
    this.selectedTime = time;
  }

  clearSelectedTime() {
    this.selectedTime = null;
  }

  setClientName(name) {
    this.clientName = name;
  }

  setClientPhoneNumber(phoneNumber) {
    this.clientPhoneNumber = phoneNumber;
  }

  setClientRemindMinutes(minutes) {
    this.clientRemindMinutes = minutes;
  }

  // setLastSelectedDate(date) {
  //   this.lastSelectedDate = date;
  // }
}

const StoreContext = createContext(new CheckboxStore());

export const useCheckboxStore = () => useContext(StoreContext);

export default StoreContext;
