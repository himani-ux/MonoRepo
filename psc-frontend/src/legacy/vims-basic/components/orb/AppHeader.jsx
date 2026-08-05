// src/components/ORBHeader.jsx
import "../../styles/orb/AppHeader.css";
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/auth/useAuth";
import { useAuthStore } from "@/stores/auth-store";

export default function ORBHeader() {
  const {user} = useAuth();
  // Note: We still get the vesselId from sessionStorage, which is set during login based on CrewID
  const storedVesselId = user?.vessel_id;
  const navigate = useNavigate();

  // Add vessel state
  const [vessel, setVessel] = useState(null);
  const [isLoadingVessel, setIsLoadingVessel] = useState(true); // Add loading state
  // Add state for sidebar visibility
  const [sidebarVisible, setSidebarVisible] = useState(false);
  // State for new entries indicators (currently hardcoded or needs external update)
  const [hasNewApproved, setHasNewApproved] = useState(false);
  const [hasNewRejected, setHasNewRejected] = useState(false);
  const [hasNewDeleted, setHasNewDeleted] = useState(false);

  // Fetch vessel details on mount and whenever storedVesselId changes
  useEffect(() => {
    setIsLoadingVessel(true); // Set loading state
    setVessel(null); // Reset vessel data while fetching

    if (!storedVesselId) {
      console.warn("ORBHeader: No vesselId found in sessionStorage.");
      setIsLoadingVessel(false); // Stop loading if no ID
      return;
    }

    // Fetch vessel details using the storedVesselId
    fetch("http://localhost:8000/api/orb/api/vessels/")
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then(data => {
        // Handle both array and paginated response
        const vesselList = Array.isArray(data) ? data : (data.results || []);

        // Find the selected vessel based on the ID from sessionStorage (case-insensitive)
        const selectedVessel = vesselList.find(v => v.id.toLowerCase() === storedVesselId.toLowerCase());

        if (selectedVessel) {
          setVessel({
            vesselName: selectedVessel.vesselName,
            imoNumber: selectedVessel.imonumber
          });
          console.log("ORBHeader: Loaded vessel details:", selectedVessel.vesselName);
        } else {
          console.warn("ORBHeader: Vessel not Found for ID from sessionStorage:", storedVesselId);
          console.warn("Available vessel IDs from API:", vesselList.map(v => v.id)); // Log all available IDs for comparison
          alert(" Vessel not found based on your crew assignment. Please contact admin.");
        }
        setIsLoadingVessel(false); // Stop loading after successful fetch/check
      })
      .catch(err => {
        console.error("ORBHeader: Network error : Cannot load vessel data.", err);
        alert(" Network error: Cannot load vessel data. Check backend.");
        setIsLoadingVessel(false); // Stop loading even if there's an error
      });
  }, [storedVesselId]); // Dependency array includes storedVesselId

  // Toggle sidebar visibility
  const toggleSidebar = () => {
    setSidebarVisible(!sidebarVisible);
  };

  // Close sidebar if clicked outside (optional)
  useEffect(() => {
    const handleClickOutside = (event) => {
      const sidebar = document.getElementById('sidebar');
      const toggleButton = document.querySelector('.sidebar-toggle');
      if (sidebar && toggleButton && !sidebar.contains(event.target) && !toggleButton.contains(event.target)) {
        setSidebarVisible(false);
      }
    };

    if (sidebarVisible) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [sidebarVisible]);

  // Logout handler
  const handleLogout = async () => {
    const confirmLogout = window.confirm("Are you sure you want to LogOut");
    if (!confirmLogout) return;

    try {
      const selectedVesselId = user.vessel_id;
      await useAuthStore.getState().logout();
      sessionStorage.clear();

      if (selectedVesselId) {
        localStorage.setItem("selectedVesselId", selectedVesselId);
      }

      alert(" Logged out successfully");
      navigate("/login", { replace: true });
    } catch (err) {
      console.error("Logout failed:", err);
      navigate("/login", { replace: true });
    }
  };

  return (
    <>
      <Sidebar
        isVisible={sidebarVisible}
        onClose={() => setSidebarVisible(false)}
        hasNewApproved={hasNewApproved}
        hasNewRejected={hasNewRejected}
        hasNewDeleted={hasNewDeleted}
      />

      <div className="app-header orb-theme">
        <div className="header-content">
          <button className="sidebar-toggle" onClick={toggleSidebar} aria-label="Open ORB navigation">
            ☰
          </button>

          <h1 className="app-title">
            <span className="title-main">E-ORB</span>
            <span className="title-sub">Logbook</span>
          </h1>

          <div className="vessel-info">
            {isLoadingVessel ? (
              "Loading vessel..."
            ) : vessel ? (
              <>
                <strong>{vessel.vesselName?.toUpperCase() || "UNKNOWN VESSEL"}</strong>
                {vessel.imoNumber ? <span>IMO {vessel.imoNumber}</span> : null}
              </>
            ) : (
              "Vessel Not Found"
            )}
          </div>

          <div className="user-section">
            <span className="greeting">
              Welcome, <strong>{user?.first_name || user?.surname ? `${user.first_name} ${user.surname}` : "USER"}</strong>
              <span className="rank"> ({user?.rank || "OFFICER"})</span>
            </span>
            <button onClick={handleLogout} className="btn-logout">
              Logout
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

function Sidebar({ isVisible, onClose, hasNewApproved, hasNewRejected, hasNewDeleted }) {
  const navigate = useNavigate();

  const handleNavigation = (path) => {
    navigate(`/orb${path}`);
    onClose();
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div id="sidebar" className="sidebar-overlay">
      <div className="sidebar-content">
        <button className="close-btn" onClick={onClose} aria-label="Close ORB navigation">×</button>
        <ul className="sidebar-menu">
          <li onClick={() => handleNavigation('/approved-entries')}>
            <span>Approved Entries</span>
            {hasNewApproved && <span className="sidebar-badge">New Entry</span>}
          </li>
          <li onClick={() => handleNavigation('/rejected-entries')}>
            <span>Rejected Entries</span>
            {hasNewRejected && <span className="sidebar-badge">New Entry</span>}
          </li>
          <li onClick={() => handleNavigation('/deleted-entries')}>
            <span>Deleted Entries</span>
            {hasNewDeleted && <span className="sidebar-badge">New Entry</span>}
          </li>
          <li onClick={() => handleNavigation('/pdf-archive')}>
            <span>Master Signed PDFs</span>
          </li>
          <li className="sidebar-menu-footer" onClick={() => handleNavigation('/orb-guidelines')}>
            <span>Guidelines</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
