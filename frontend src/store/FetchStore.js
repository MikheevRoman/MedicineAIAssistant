import { makeObservable, observable, action } from 'mobx';
// import axios from 'axios';
import medicsDataFromMyJson from "../Medics.json"
import workedDaysDataFromMyJson from "../Time.json"
import institutionDataFromMyJson from "../Institution.json"

class FetchStore {
    medicsData = {};
    medicsData = medicsDataFromMyJson;

    workedDaysData = [];
    workedDaysData = workedDaysDataFromMyJson;

    institutionData = [];
    institutionData = institutionDataFromMyJson;


    isMedicDataLoaded = false;

    constructor() {
        makeObservable(this, {
            medicsData: observable,
            workedDaysData: observable,
            institutionData: observable,
            isMedicDataLoaded: observable,
            // fetchMedicsData: action,
            // fetchWorkedDaysData: action,
            setMedicsData: action
        }, { deep: true, });
    }

    setMedicsData = (newData) => {
        this.medicsData = newData;
    }

}

const fetchStore = new FetchStore();

export default fetchStore;
