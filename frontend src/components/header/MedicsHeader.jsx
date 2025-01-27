import React from "react";
import { Title1 } from "../../textStyles/TextStyleComponents";
import cl from "./MedicsHeader.module.css";

const MedicsHeader = ({ children }) => {

    return (
        <div className={cl.header}>
            <Title1>{children}</Title1>
        </div>
    )
}



export default MedicsHeader;