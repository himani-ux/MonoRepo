// src/components/ORBFooter.jsx
import React from "react";
import "../../styles/orb/ORBFooter.css";

export default function AppFooter() {
  return (
    <div className="app-footer">
      <p>
        © {new Date().getFullYear()} E-Oil Record Book logbook | 
        <span className="footer-tagline"> @Cymsol Marine Services LLP</span>
      </p>
    </div>
  );
}