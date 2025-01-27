import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./App.css";
import Medics from "./pages/medicsPage/MedicsPage";
import Info from "./pages/info/Info";
import SelectTime from "./pages/SelectTime";
import LastStep from "./pages/lastStep/LastStep";
import ErrorPage from "./pages/errorPage/ErrorPage";
import MedicalOrganization from "./pages/medicalOrganization/MedicalOrganization";
import InfoInstitution from "./pages/info/infoInstitution/InfoInstitution";

function App() {

  useEffect(() => {
    document.title = "Client";
    if (window.Telegram.WebApp) {
      window.Telegram.WebApp.ready();
    }
  }, []);


  return (
    <BrowserRouter>
      <Routes>
        <Route path="*" element={<MedicalOrganization />} />
        <Route path="/medics" element={<Medics />} />
        <Route path="/info/:id" element={<Info />} />
        <Route path="/infoInstitution/:id" element={<InfoInstitution />} />
        <Route path="/selectTime" element={<SelectTime />} />
        <Route path="/lastStep" element={<LastStep />} />
        <Route path="/errorPage" element={<ErrorPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;