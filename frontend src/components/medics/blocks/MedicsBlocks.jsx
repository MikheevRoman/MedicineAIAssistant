import React from "react";
// import axios from "axios";
import { Footnote } from "../../../textStyles/TextStyleComponents";
import MedicsList from "../list/MedicsList";
import cl from "./MedicsBlocks.module.css";
import clForLastChild from "../list/MedicsList.module.css";
// import { useState, useEffect } from "react";
// import CryptoJS from "crypto-js";
import { observer } from "mobx-react-lite";
import fetchStore from "../../../store/FetchStore";



const MedicsBlocks = observer(({ isInstitution = false }) => {
    const medicsEntries = Object.entries(fetchStore.medicsData);



    return (
        <div>
            {isInstitution ? (
                medicsEntries.map(([category, items]) => (
                    <div key={category} className={cl.block}>
                        <Footnote className={cl.blockName}>{category}</Footnote>
                        <div className={cl.list}>
                            {items.map(medic => (
                                <div key={medic.id} className={clForLastChild.containerForLastChild}>
                                    <MedicsList
                                        medics={{
                                            id: medic.id,
                                            name: medic.name,
                                            price: medic.price,
                                            duration: medic.duration, // Обратите внимание на изменение 'time' на 'duration'
                                            info: medic.description, // Изменение 'info' на 'description'
                                            category: medic.category
                                        }}
                                        isInstitution={isInstitution}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                ))
            ) : (
                <div className={cl.list}>
                    {fetchStore.institutionData.map(medic => (
                        <div key={medic.id} className={clForLastChild.containerForLastChild}>
                            <MedicsList
                                medics={{
                                    id: medic.id,
                                    name: medic.name,
                                    address: medic.address,

                                }}
                            />
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
})

export default MedicsBlocks;