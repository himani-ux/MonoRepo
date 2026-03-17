import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import AllEntriesView from '../../pages/orb/AllEntriesView';
import ApprovedEntriesView from '../../pages/orb/ApprovedEntriesView'; 
import RejectedEntriesView from '../../pages/orb/RejectedEntriesView';
import DeletedEntriesView from '../../pages/orb/DeletedEntriesView';
import PDFArchive from "../../pages/orb/PDFArchive";
import GuidelinesPage from "../../pages/orb/GuidelinesPage";
import Dashboard from "../../pages/orb/Dashboard"; 

export default function OrbRoutes() {
  return (
    <>
      <ToastContainer position="top-right" autoClose={3000} theme="colored" />
      <Routes>
        <Route path="/" element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        
        <Route path="all-entries" element={<AllEntriesView />} />
        <Route path="approved-entries" element={<ApprovedEntriesView />} /> 
        <Route path="rejected-entries" element={<RejectedEntriesView />} /> 
        <Route path="deleted-entries" element={<DeletedEntriesView />} />
        <Route path="pdf-archive" element={<PDFArchive/>}/>
        <Route path="orb-guidelines" element={<GuidelinesPage/>}/>
      </Routes>
    </>
  );
}