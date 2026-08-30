import React, { createContext, useState, useContext } from 'react';

const translations = {
  en: {
    dashboard: "Command Center",
    cameras: "Camera Management",
    alerts: "Alert Center",
    analytics: "Analytics Dashboard",
    watchlist: "Watchlist Management",
    map: "Geospatial View",
    evidence: "Evidence Vault",
    settings: "System Settings",
    active_cameras: "Active Cameras",
    humans_detected: "Humans Detected",
    vehicles_detected: "Vehicles Detected",
    alerts_today: "Alerts Today",
    total_cameras: "Total Cameras",
    language: "Language",
    english: "English",
    hindi: "Hindi",
  },
  hi: {
    dashboard: "कमांड सेंटर",
    cameras: "कैमरा प्रबंधन",
    alerts: "अलर्ट सेंटर",
    analytics: "एनालिटिक्स डैशबोर्ड",
    watchlist: "वाचलिस्ट प्रबंधन",
    map: "भू-स्थानिक दृश्य",
    evidence: "सबूत वॉल्ट",
    settings: "सिस्टम सेटिंग्स",
    active_cameras: "सक्रिय कैमरे",
    humans_detected: "मनुष्य का पता चला",
    vehicles_detected: "वाहन का पता चला",
    alerts_today: "आज के अलर्ट",
    total_cameras: "कुल कैमरे",
    language: "भाषा",
    english: "अंग्रेज़ी",
    hindi: "हिंदी",
  }
};

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState('en');

  const t = (key) => translations[language][key] || key;

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
