// // src/components/MainDashboard.jsx
// import React, { useState, useEffect } from 'react';
// import { useNavigate, Link, useLocation } from 'react-router-dom';
// import ApprovedNotificationsLibrary from './ApprovedNotificationsLibrary'; // Import the existing library component
// import { hasPermission } from '../../utils/circular/permissionUtils';; // Import the utility function

// const MainDashboard = () => {
//     const navigate = useNavigate();
//     const location = useLocation();

//     // Retrieve user data from localStorage
//     const userStringFromStorage = localStorage.getItem('user');
//     console.log("MainDashboard: Raw user string from localStorage:", userStringFromStorage); // Log raw string

//     const user = JSON.parse(userStringFromStorage);
//     console.log("MainDashboard: Parsed user object from localStorage:", user); // Log parsed object
//     console.log("MainDashboard: user.user_type:", user?.user_type); // Log the specific property

//     if (!user) {
//         // If no user is found in localStorage, redirect to login
//         console.error("MainDashboard: No user found in localStorage. Redirecting to login.");
//         navigate('/login', { replace: true });
//         return null;
//     }

//     // Ensure user is an office user for this component
//     console.log("MainDashboard: Checking user_type against 'office'. Current user_type:", user.user_type); // Log the check
//     if (user.user_type !== 'office') {
//         console.error("MainDashboard: Access denied for non-office user. Redirecting to login.");
//         console.log("MainDashboard: Full user object that failed the check:", user); // Log the full object
//         navigate('/login', { replace: true });
//         return null; // Return null while redirecting
//     }
//     console.log("MainDashboard: User is an office user. Proceeding with render."); // Log successful check


//     const userName = user.display_name || user.employee_id || user.crew_id;
//     const userType = user.user_type; // Should be 'office'
//     const userRoleName = user.role_name || user.role;
//     const userWorkSide = user.work_side;

//     console.log("MainDashboard: User Type:", userType, "User Name:", userName, "User Role Name:", userRoleName, "User Work Side:", userWorkSide);

//     // --- Example: Logout function ---
//     const handleLogout = () => {
//         console.log("MainDashboard: Logging out user.");
//         localStorage.clear();
//         sessionStorage.clear();
//         navigate('/login', { replace: true });
//     };

//     // --- Navbar Tabs ---6
//     const renderNavbarTabs = () => {
//         if (userWorkSide === undefined) {
//             console.warn("MainDashboard: work_side not found in user object. Hiding tabs.");
//             return null;
//         }

//         if (userWorkSide === 1) {
//             console.log("MainDashboard: work_side is 1 (ship side). Hiding tabs.");
//             return null;
//         }

//         console.log("MainDashboard: work_side is 0 (office side). Showing tabs.");
//         return (
//             <div className="flex items-center gap-2">
//                 {/* Office User Link - Use WithPermission if needed */}
//                 {/* <Link
//                     to="office"
//                     className={`p-2 rounded-full hover:bg-gray-100 text-gray-600 ${
//                         location.pathname === '/circular/office' ? 'bg-gray-200' : ''
//                     }`}
//                     aria-label="Go to Office User Panel"
//                     title="Office User Panel"
//                 >
//                     <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus-square-fill" viewBox="0 0 16 16">
//                         <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2zm6.5 4.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3a.5.5 0 0 1 1 0" />
//                     </svg>
//                 </Link> */}

//                 <Link
//   to="/circular/office"
//   className={`p-2 rounded-full hover:bg-gray-100 text-gray-600 ${
//     location.pathname === '/circular/office' ? 'bg-gray-200' : ''
//   }`}
//   aria-label="Go to Office User Panel"
//   title="Office User Panel"
// >
//   <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
//        className="bi bi-plus-square-fill" viewBox="0 0 16 16">
//     <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2zm6.5 4.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3a.5.5 0 0 1 1 0"/>
//   </svg>
// </Link>


//                 {/* Admin All Notifications Link */}
//                 {(userType === 'office' && user.role_name?.toLowerCase() === 'admin') && (
//                     <Link
//   to="/circular/admin/all-notifications"
//   className={`p-2 rounded-full hover:bg-gray-100 text-gray-600 ${
//     location.pathname === "/circular/admin/all-notifications"
//       ? "bg-gray-200"
//       : ""
//   }`}
//   aria-label="View all notifications"
//   title="View All Notifications"
// >
//   <svg
//     xmlns="http://www.w3.org/2000/svg"
//     width="16"
//     height="16"
//     fill="currentColor"
//     className="bi bi-wallet"
//     viewBox="0 0 16 16"
//   >
//     <path d="M0 3a2 2 0 0 1 2-2h13.5a.5.5 0 0 1 0 1H15v2a1 1 0 0 1 1 1v8.5a1.5 1.5 0 0 1-1.5 1.5h-12A2.5 2.5 0 0 1 0 12.5zm1 1.732V12.5A1.5 1.5 0 0 0 2.5 14h12a.5.5 0 0 0 .5-.5V5H2a2 2 0 0 1-1-.268M1 3a1 1 0 0 0 1 1h12V2H2a1 1 0 0 0-1 1" />
//   </svg>
// </Link>

//                 )}

//                 {/* User Notification Link - Use WithPermission if needed */}
//                <Link
//   to="/circular/user/notifications"
//   className={`p-2 rounded-full hover:bg-gray-100 text-gray-600 ${
//     location.pathname === "/circular/user/notifications"
//       ? "bg-gray-200"
//       : ""
//   }`}
//   aria-label="View your notifications"
//   title="View Your Notification"
// >
//   <svg
//     xmlns="http://www.w3.org/2000/svg"
//     width="16"
//     height="16"
//     fill="currentColor"
//     className="bi bi-hourglass-split"
//     viewBox="0 0 16 16"
//   >
//     <path d="M2.5 15a.5.5 0 1 1 0-1h1v-1a4.5 4.5 0 0 1 2.557-4.06c.29-.139.443-.377.443-.59v-.7c0-.213-.154-.451-.443-.59A4.5 4.5 0 0 1 3.5 3V2h-1a.5.5 0 0 1 0-1h11a.5.5 0 0 1 0 1h-1v1a4.5 4.5 0 0 1-2.557 4.06c-.29.139-.443.377-.443.59v.7c0 .213.154.451.443.59A4.5 4.5 0 0 1 12.5 13v1h1a.5.5 0 0 1 0 1" />
//   </svg>
// </Link>


//                 {/* Draft Notification Link - Use WithPermission if needed */}
//                <Link
//   to="/circular/user/drafts"
//   className={`p-2 rounded-full hover:bg-gray-100 text-gray-600 ${
//     location.pathname === "/circular/user/drafts"
//       ? "bg-gray-200"
//       : ""
//   }`}
//   aria-label="View draft notifications"
//   title="View Draft Notifications"
// >
//   <svg
//     xmlns="http://www.w3.org/2000/svg"
//     width="16"
//     height="16"
//     fill="currentColor"
//     className="bi bi-pencil"
//     viewBox="0 0 16 16"
//   >
//     <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207z" />
//   </svg>
// </Link>

//             </div>
//         );
//     };
//     // --- END Navbar Tabs ---


//     // --- Example: Footer Component (inline or separate) ---
//     const Footer = () => (
//         <footer className="bg-gray-800 text-white py-4 mt-auto">
//             <div className="container mx-auto px-4 text-center text-sm">
//                 <p>&copy; {new Date().getFullYear()} KSM Circulars. All rights reserved.</p>
//                 <div className="mt-2 space-x-4">
//                     <a href="#terms" className="hover:text-gray-300">Terms of Service</a>
//                     <a href="#privacy" className="hover:text-gray-300">Privacy Policy</a>
//                     <a href="#support" className="hover:text-gray-300">Support</a>
//                 </div>
//             </div>
//         </footer>
//     );


//     return (
//         <div className="min-h-screen flex flex-col bg-gray-50">
//             {/* --- Navbar --- */}
//             <nav className="bg-gradient-to-r from-sky-50 via-sky-100 to-slate-100 border-b border-slate-200 sticky top-0 z-50 shadow-sm">
//                 <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
//                     <span className="font-semibold text-lg">KSM Circulars (Office)</span>
//                     <div className="flex items-center gap-4">
//                         {renderNavbarTabs()}
//                         <span className="text-sm text-gray-600">
//                             Welcome, {userName}!
//                         </span>
//                         <button
//                             onClick={handleLogout}
//                             className="px-3 py-1 bg-red-600 text-white rounded text-xs font-medium hover:bg-red-700 transition"
//                             aria-label="Logout"
//                         >
//                             Logout
//                         </button>
//                     </div>
//                 </div>
//             </nav>
//             {/* --- END Navbar --- */}

//             {/* --- Main Content Area --- */}
//             <main className="flex-grow p-6">
//                 <ApprovedNotificationsLibrary />
//             </main>
//             {/* --- END Main Content Area --- */}

//             {/* --- Footer --- */}
//             <Footer />
//             {/* --- END Footer --- */}
//         </div>
//     );
// };

// export default MainDashboard;

//---------------------------------------VERSION 2.0---------------------------------------//

// src/components/MainDashboard.jsx
import React from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import ApprovedNotificationsLibrary from './ApprovedNotificationsLibrary';
import { hasPermission } from '../../utils/circular/permissionUtils';
import PageLayout from '../../components/layout/PageLayout'; // Import PageLayout
import { useAuth } from '../../hooks/auth/useAuth'; // Import useAuth hook
import { useAuthStore } from '@/stores/auth-store';

const MainDashboard = () => {
    const navigate = useNavigate();
    const location = useLocation();



    const { user } = useAuth();
    console.log("MainDashboard: Parsed user object from localStorage:", user);
    console.log("MainDashboard: user.user_type:", user?.user_type);

    if (!user) {
        console.error("MainDashboard: No user found in localStorage. Redirecting to login.");
        navigate('/login', { replace: true });
        return null;
    }

    // Ensure user is an office user for this component
    console.log("MainDashboard: Checking user_type against 'office'. Current user_type:", user.user_type);
    if (user.user_type !== 'office') {
        console.error("MainDashboard: Access denied for non-office user. Redirecting to login.");
        console.log("MainDashboard: Full user object that failed the check:", user);
        navigate('/login', { replace: true });
        return null;
    }
    console.log("MainDashboard: User is an office user. Proceeding with render.");

    const userName = user.display_name || user.employee_id || user.crew_id;
    const userType = user.user_type;
    const userRoleName = user.role_name || user.role;
    const userWorkSide = user.work_side;

    console.log("MainDashboard: User Type:", userType, "User Name:", userName, "User Role Name:", userRoleName, "User Work Side:", userWorkSide);

    // --- Logout function ---
    const handleLogout = async () => {
        await useAuthStore.getState().logout();
        sessionStorage.clear();
        navigate('/login', { replace: true });
    };

    // --- Navbar Tabs ---
    const renderNavbarTabs = () => {
        if (userWorkSide === undefined) {
            console.warn("MainDashboard: work_side not found in user object. Hiding tabs.");
            return null;
        }

        if (userWorkSide === 1) {
            console.log("MainDashboard: work_side is 1 (ship side). Hiding tabs.");
            return null;
        }

        console.log("MainDashboard: work_side is 0 (office side). Showing tabs.");
        return (
            <div className="flex items-center gap-2">
                {/* Office User Link */}
                <Link
                    to="/circular/office"
                    className={`p-2 rounded-full hover:bg-gray-100 text-gray-600 ${
                        location.pathname === '/circular/office' ? 'bg-gray-200' : ''
                    }`}
                    aria-label="Go to Office User Panel"
                    title="Office User Panel"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
                         className="bi bi-plus-square-fill" viewBox="0 0 16 16">
                        <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2zm6.5 4.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3a.5.5 0 0 1 1 0"/>
                    </svg>
                </Link>

                {/* Admin All Notifications Link */}
                {(userType === 'office' && user.role_name?.toLowerCase() === 'admin') && (
                    <Link
                        to="/circular/admin/all-notifications"
                        className={`p-2 rounded-full hover:bg-gray-100 text-gray-600 ${
                            location.pathname === "/circular/admin/all-notifications"
                                ? "bg-gray-200"
                                : ""
                        }`}
                        aria-label="View all notifications"
                        title="View All Notifications"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            fill="currentColor"
                            className="bi bi-wallet"
                            viewBox="0 0 16 16"
                        >
                            <path d="M0 3a2 2 0 0 1 2-2h13.5a.5.5 0 0 1 0 1H15v2a1 1 0 0 1 1 1v8.5a1.5 1.5 0 0 1-1.5 1.5h-12A2.5 2.5 0 0 1 0 12.5zm1 1.732V12.5A1.5 1.5 0 0 0 2.5 14h12a.5.5 0 0 0 .5-.5V5H2a2 2 0 0 1-1-.268M1 3a1 1 0 0 0 1 1h12V2H2a1 1 0 0 0-1 1" />
                        </svg>
                    </Link>
                )}

                {/* User Notification Link */}
                <Link
                    to="/circular/user/notifications"
                    className={`p-2 rounded-full hover:bg-gray-100 text-gray-600 ${
                        location.pathname === "/circular/user/notifications"
                            ? "bg-gray-200"
                            : ""
                    }`}
                    aria-label="View your notifications"
                    title="View Your Notification"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        fill="currentColor"
                        className="bi bi-hourglass-split"
                        viewBox="0 0 16 16"
                    >
                        <path d="M2.5 15a.5.5 0 1 1 0-1h1v-1a4.5 4.5 0 0 1 2.557-4.06c.29-.139.443-.377.443-.59v-.7c0-.213-.154-.451-.443-.59A4.5 4.5 0 0 1 3.5 3V2h-1a.5.5 0 0 1 0-1h11a.5.5 0 0 1 0 1h-1v1a4.5 4.5 0 0 1-2.557 4.06c-.29.139-.443.377-.443.59v.7c0 .213.154.451.443.59A4.5 4.5 0 0 1 12.5 13v1h1a.5.5 0 0 1 0 1" />
                    </svg>
                </Link>

                {/* Draft Notification Link */}
                <Link
                    to="/circular/user/drafts"
                    className={`p-2 rounded-full hover:bg-gray-100 text-gray-600 ${
                        location.pathname === "/circular/user/drafts"
                            ? "bg-gray-200"
                            : ""
                    }`}
                    aria-label="View draft notifications"
                    title="View Draft Notifications"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        fill="currentColor"
                        className="bi bi-pencil"
                        viewBox="0 0 16 16"
                    >
                        <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207z" />
                    </svg>
                </Link>
            </div>
        );
    };

    // --- Custom Footer ---
    const customFooter = (
        <footer className="bg-gray-200 text-black py-4">
            <div className="container mx-auto px-4 text-center text-sm">
                <p>&copy; {new Date().getFullYear()} KSM Circulars. All rights reserved.</p>
                <div className="mt-2 space-x-4">
                    <a href="#terms" className="hover:text-red-500">Terms of Service</a>
                    <a href="#privacy" className="hover:text-red-500">Privacy Policy</a>
                    <a href="#support" className="hover:text-red-500">Support</a>
                </div>
            </div>
        </footer>
    );

    // --- Custom Header Right Content (tabs + welcome + logout) ---
    const headerRightContent = (
        <div className="flex items-center gap-4">
            {renderNavbarTabs()}
            {/* <span className="text-sm text-gray-600">
                Welcome, {userName}!
            </span> */}
            {/* <button
                onClick={handleLogout}
                className="px-3 py-1 bg-red-600 text-white rounded text-xs font-medium hover:bg-red-700 transition"
                aria-label="Logout"
            >
                Logout
            </button> */}
        </div>
    );

    return (
       
            <div className="bg-gray-50 min-h-full">
                <ApprovedNotificationsLibrary />
            </div>
      
    );
};

export default MainDashboard;
