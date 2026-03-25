// // src/components/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import FilterBar from '../../components/circular/FilterBar';
import KsmLibrary from '../../components/circular/KsmLibrary';
import PdfViewer from '../../components/circular/PdfViewer';
import PageLayout from '../../components/layout/PageLayout';
import { useAuth } from '../../hooks/auth/useAuth';
import { useAuthStore } from '@/stores/auth-store';

// 🔑 MAP BACKEND IDs TO MEANINGFUL NAMES
const FORM_ID_MAP = {
  PSC_F_012: 'FILTERS',
  PSC_F_013: 'NOTIFICATIONS',
};

const PROCESS_ID_MAP = {
  PSC_P_028: 'VIEW_FILTERS',
  PSC_P_029: 'DOWNLOAD_PDF',
  PSC_P_030: "P_VIEW_LIST",
  PSC_P_031: "P_VIEW_DETAIL", 
  PSC_P_032: "P_ACKNOWLEDGE",
  PSC_P_033: "P_VIEW_CREW",
  PSC_P_034: "P_REMIND_CREW",
  PSC_P_035: "P_DOWNLOAD_PDF",
  PSC_P_036: "P_ACCESS_PDF",
};

const normalizePermissionId = (id, type) => {
  const normalized = String(id || '').trim().toUpperCase();
  if (!normalized) return '';

  if (type === 'form') {
    if (normalized.startsWith('PSC_F_')) return normalized;
    if (normalized.startsWith('F_')) return `PSC_${normalized}`;
    return normalized;
  }

  if (normalized.startsWith('PSC_P_')) return normalized;
  if (normalized.startsWith('P_')) return `PSC_${normalized}`;
  return normalized;
};

const Dashboard = () => {
  const navigate = useNavigate();
  
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // 🔥 VIEW STATE MANAGEMENT (only state, no API logic)
  const [viewMode, setViewMode] = useState('list');
  const [selectedNotification, setSelectedNotification] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [scope, setScope] = useState(["SEQ", "Technical"]); // ✅ Default values
  const [selectedTypes, setSelectedTypes] = useState(["Alert", "Circular", "Work Instruction"]); // ✅
  const [selectedCriticalities, setSelectedCriticalities] = useState(["Critical", "High", "Medium", "Low"]); // ✅
  const [onlyUnread, setOnlyUnread] = useState(false);

      // Get user data for header
    const {user: currentUser} = useAuth();
    const userName = currentUser?.display_name || currentUser?.employee_id || currentUser?.crew_id;

    // Logout handler
    const handleLogout = async () => {
        await useAuthStore.getState().logout();
        sessionStorage.clear();
        navigate('/login', { replace: true });
    };

  // 🔐 Permission checker
  const hasPermission = (formKey, processKey) => {
    if (!user) return false;
    const formId = Object.keys(FORM_ID_MAP).find(id => FORM_ID_MAP[id] === formKey);
    const processId = Object.keys(PROCESS_ID_MAP).find(id => PROCESS_ID_MAP[id] === processKey);
    const normalizedFormIds = (user.form_ids ?? []).map((id) => normalizePermissionId(id, 'form'));
    const normalizedProcessIds = (user.process_ids ?? []).map((id) => normalizePermissionId(id, 'process'));
    return (
      !!formId &&
      !!processId &&
      normalizedFormIds.includes(normalizePermissionId(formId, 'form')) &&
      normalizedProcessIds.includes(normalizePermissionId(processId, 'process'))
    );
  };

  // 🔄 Toggle handlers
  const toggleScope = (item) => setScope(prev => prev.includes(item) ? prev.filter(i => i !== item) : [...prev, item]);
  const toggleType = (item) => setSelectedTypes(prev => prev.includes(item) ? prev.filter(i => i !== item) : [...prev, item]);
  const toggleCriticality = (item) => setSelectedCriticalities(prev => prev.includes(item) ? prev.filter(i => i !== item) : [...prev, item]);

  // 🚀 Initialize dashboard (ONLY permission fetch)
  useEffect(() => {
    // ✅ SIMPLE USER LOADING FROM LOCALSTORAGE
    const storedUser = currentUser
    if (!storedUser) {
      navigate('/login', { replace: true });
      return;
    }
    
    // ✅ USER ALREADY HAS PERMISSIONS FROM LOGIN RESPONSE
    setUser(storedUser);
    setLoading(false);
  }, [navigate]);

  // 🖼️ Render
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center"><p>Loading dashboard...</p></div>;
  }
  if (!user) return null;

  // ✅ Permission flags
  const canUseSearch = hasPermission('FILTERS', 'VIEW_FILTERS');
  const canUseDeptFilter = hasPermission('FILTERS', 'VIEW_FILTERS');
  const canUseTypeFilter = hasPermission('FILTERS', 'VIEW_FILTERS');
  const canUseCriticalityFilter = hasPermission('FILTERS', 'VIEW_FILTERS');
  const canUseUnreadToggle = hasPermission('FILTERS', 'VIEW_FILTERS');
  const canUseDownload = hasPermission('FILTERS', 'DOWNLOAD_PDF');

  const canViewDetail = hasPermission('NOTIFICATIONS', 'P_VIEW_DETAIL');
  const canAcknowledge = hasPermission('NOTIFICATIONS', 'P_ACKNOWLEDGE');
  const canViewList = hasPermission('NOTIFICATIONS', 'P_VIEW_LIST');
  const canRemindCrew = hasPermission('NOTIFICATIONS', 'P_REMIND_CREW');
  const canDownloadPdf = hasPermission('NOTIFICATIONS', 'P_DOWNLOAD_PDF');
  const canViewCrewStatus = hasPermission('NOTIFICATIONS', 'P_VIEW_CREW');
  const canAccessPdf = hasPermission('NOTIFICATIONS', 'P_ACCESS_PDF');

  // 🔥 VIEW HANDLERS (no API logic, just state changes)
  const handleViewPdf = (notification) => {
    if (!canAccessPdf) return;
    setSelectedNotification(notification);
    setViewMode('pdf');
  };

  const handleBackToList = () => {
    setViewMode('list');
    setSelectedNotification(null);
  };

  

  return (
    <>
           
      {viewMode === 'list' && (
        <FilterBar
          user={user}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          scope={scope}
          onToggleScope={toggleScope}
          selectedTypes={selectedTypes}
          onToggleType={toggleType}
          selectedCriticalities={selectedCriticalities}
          onToggleCriticality={toggleCriticality}
          onlyUnread={onlyUnread}
          onToggleOnlyUnread={setOnlyUnread}
          canUseSearch={canUseSearch}
          canUseDeptFilter={canUseDeptFilter}
          canUseTypeFilter={canUseTypeFilter}
          canUseCriticalityFilter={canUseCriticalityFilter}
          canUseUnreadToggle={canUseUnreadToggle}
          canUseDownload={canUseDownload}
        />
      )}

      {viewMode === 'list' && (
        <KsmLibrary
          user={user}
          canViewList={canViewList}
          canViewDetail={canViewDetail}
          canAcknowledge={canAcknowledge}
          canViewCrewStatus={canViewCrewStatus}
          canRemindCrew={canRemindCrew}
          canDownloadPdf={canDownloadPdf}
          canAccessPdf={canAccessPdf}
          onViewPdf={handleViewPdf}

          searchTerm={searchTerm}
          scope={scope}
          selectedTypes={selectedTypes}
          selectedCriticalities={selectedCriticalities}
          onlyUnread={onlyUnread}
        />
      )}

      {viewMode === 'pdf' && selectedNotification && (
        <PdfViewer
          user={user}
          notification={selectedNotification}
          onAcknowledge={canAcknowledge ? (notification) => {
            // Acknowledgment API call will be handled in PdfViewer
          } : undefined}
          onBack={handleBackToList}
          canAcknowledge={canAcknowledge}
          canDownload={canDownloadPdf}
        />
      )}

      </>
   
  );
};

export default Dashboard;


// src/components/Dashboard.jsx
// src/components/Dashboard.jsx
// import React, { useState, useEffect } from 'react';
// import { useNavigate } from 'react-router-dom';
// import FilterBar from './FilterBar';
// import KsmLibrary from './KsmLibrary';
// import PdfViewer from './PdfViewer';
// import PageLayout from '../layout/PageLayout';

// // 🔑 MAP BACKEND IDs TO MEANINGFUL NAMES
// const FORM_ID_MAP = {
//   PSC_F_012: 'FILTERS',
//   PSC_F_013: 'NOTIFICATIONS',
// };

// const PROCESS_ID_MAP = {
//   PSC_P_028: 'VIEW_FILTERS',
//   PSC_P_029: 'DOWNLOAD_PDF',
//   PSC_P_030: "P_VIEW_LIST",
//   PSC_P_031: "P_VIEW_DETAIL", 
//   PSC_P_032: "P_ACKNOWLEDGE",
//   PSC_P_033: "P_VIEW_CREW",
//   PSC_P_034: "P_REMIND_CREW",
//   PSC_P_035: "P_DOWNLOAD_PDF",
//   PSC_P_036: "P_ACCESS_PDF",
// };

// const Dashboard = () => {
//   const navigate = useNavigate();
  
//   const [user, setUser] = useState(null);
//   const [loading, setLoading] = useState(true);
  
//   // 🔥 VIEW STATE MANAGEMENT (only state, no API logic)
//   const [viewMode, setViewMode] = useState('list');
//   const [selectedNotification, setSelectedNotification] = useState(null);

//   const [searchTerm, setSearchTerm] = useState('');
//   const [scope, setScope] = useState(["SEQ", "Technical"]); // ✅ Default values
//   const [selectedTypes, setSelectedTypes] = useState(["Alert", "Circular", "Work Instruction"]); // ✅
//   const [selectedCriticalities, setSelectedCriticalities] = useState(["Critical", "High", "Medium", "Low"]); // ✅
//   const [onlyUnread, setOnlyUnread] = useState(false);

//   // Get user data for header
//   const userStringFromStorage = localStorage.getItem('user');
//   const currentUser = userStringFromStorage ? JSON.parse(userStringFromStorage) : null;
//   const userName = currentUser?.display_name || currentUser?.employee_id || currentUser?.crew_id;

//   // Logout handler
//   const handleLogout = () => {
//     console.log("Dashboard: Logging out user.");
//     localStorage.clear();
//     sessionStorage.clear();
//     navigate('/login', { replace: true });
//   };

//   // 🔐 Permission checker
//   const hasPermission = (formKey, processKey) => {
//     if (!user) return false;
//     const formId = Object.keys(FORM_ID_MAP).find(id => FORM_ID_MAP[id] === formKey);
//     const processId = Object.keys(PROCESS_ID_MAP).find(id => PROCESS_ID_MAP[id] === processKey);
//     return formId && processId && user.form_ids?.includes(formId) && user.process_ids?.includes(processId);
//   };

//   // 🔄 Toggle handlers
//   const toggleScope = (item) => setScope(prev => prev.includes(item) ? prev.filter(i => i !== item) : [...prev, item]);
//   const toggleType = (item) => setSelectedTypes(prev => prev.includes(item) ? prev.filter(i => i !== item) : [...prev, item]);
//   const toggleCriticality = (item) => setSelectedCriticalities(prev => prev.includes(item) ? prev.filter(i => i !== item) : [...prev, item]);

//   // 🚀 Initialize dashboard (ONLY permission fetch)
//   useEffect(() => {
//     // ✅ SIMPLE USER LOADING FROM LOCALSTORAGE
//     const storedUser = JSON.parse(localStorage.getItem('user'));
//     if (!storedUser) {
//       navigate('/login', { replace: true });
//       return;
//     }
    
//     // ✅ USER ALREADY HAS PERMISSIONS FROM LOGIN RESPONSE
//     setUser(storedUser);
//     setLoading(false);
//   }, [navigate]);

//   // 🖼️ Render
//   if (loading) {
//     return <div className="min-h-screen flex items-center justify-center"><p>Loading dashboard...</p></div>;
//   }
//   if (!user) return null;

//   // ✅ Permission flags
//   const canUseSearch = hasPermission('FILTERS', 'VIEW_FILTERS');
//   const canUseDeptFilter = hasPermission('FILTERS', 'VIEW_FILTERS');
//   const canUseTypeFilter = hasPermission('FILTERS', 'VIEW_FILTERS');
//   const canUseCriticalityFilter = hasPermission('FILTERS', 'VIEW_FILTERS');
//   const canUseUnreadToggle = hasPermission('FILTERS', 'VIEW_FILTERS');
//   const canUseDownload = hasPermission('FILTERS', 'DOWNLOAD_PDF');

//   const canViewDetail = hasPermission('NOTIFICATIONS', 'P_VIEW_DETAIL');
//   const canAcknowledge = hasPermission('NOTIFICATIONS', 'P_ACKNOWLEDGE');
//   const canViewList = hasPermission('NOTIFICATIONS', 'P_VIEW_LIST');
//   const canRemindCrew = hasPermission('NOTIFICATIONS', 'P_REMIND_CREW');
//   const canDownloadPdf = hasPermission('NOTIFICATIONS', 'P_DOWNLOAD_PDF');
//   const canViewCrewStatus = hasPermission('NOTIFICATIONS', 'P_VIEW_CREW');
//   const canAccessPdf = hasPermission('NOTIFICATIONS', 'P_ACCESS_PDF');

//   // 🔥 VIEW HANDLERS (no API logic, just state changes)
//   const handleViewPdf = (notification) => {
//     if (!canAccessPdf) return;
//     setSelectedNotification(notification);
//     setViewMode('pdf');
//   };

//   const handleBackToList = () => {
//     setViewMode('list');
//     setSelectedNotification(null);
//   };

//   return (
//     <PageLayout
//       userName={userName}
//       onLogout={handleLogout}
//       customTitle="KSM Circulars"
//       showBreadcrumbs={false}
//     >
//       {/* FilterBar as separate row below header */}
//       {viewMode === 'list' && (
//         <div className="bg-white border-b px-4 py-3">
//           <FilterBar
//             user={user}
//             searchTerm={searchTerm}
//             onSearchChange={setSearchTerm}
//             scope={scope}
//             onToggleScope={toggleScope}
//             selectedTypes={selectedTypes}
//             onToggleType={toggleType}
//             selectedCriticalities={selectedCriticalities}
//             onToggleCriticality={toggleCriticality}
//             onlyUnread={onlyUnread}
//             onToggleOnlyUnread={setOnlyUnread}
//             canUseSearch={canUseSearch}
//             canUseDeptFilter={canUseDeptFilter}
//             canUseTypeFilter={canUseTypeFilter}
//             canUseCriticalityFilter={canUseCriticalityFilter}
//             canUseUnreadToggle={canUseUnreadToggle}
//             canUseDownload={canUseDownload}
//           />
//         </div>
//       )}

//       {/* Main content area */}
//       {viewMode === 'list' && (
//         <KsmLibrary
//           user={user}
//           canViewList={canViewList}
//           canViewDetail={canViewDetail}
//           canAcknowledge={canAcknowledge}
//           canViewCrewStatus={canViewCrewStatus}
//           canRemindCrew={canRemindCrew}
//           canDownloadPdf={canDownloadPdf}
//           onViewPdf={handleViewPdf}
//           searchTerm={searchTerm}
//           scope={scope}
//           selectedTypes={selectedTypes}
//           selectedCriticalities={selectedCriticalities}
//           onlyUnread={onlyUnread}
//         />
//       )}

//       {viewMode === 'pdf' && selectedNotification && (
//         <PdfViewer
//           user={user}
//           notification={selectedNotification}
//           onAcknowledge={canAcknowledge ? (notification) => {
//             // Acknowledgment API call will be handled in PdfViewer
//           } : undefined}
//           onBack={handleBackToList}
//           canAcknowledge={canAcknowledge}
//           canDownload={canDownloadPdf}
//         />
//       )}
//     </PageLayout>
//   );
// };

// export default Dashboard;
