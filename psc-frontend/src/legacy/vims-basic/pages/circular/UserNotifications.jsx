// src/components/UserNotifications.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PageLayout from '../../components/layout/PageLayout';
import { useAuth } from "../../hooks/auth/useAuth";
import { useAuthStore } from '@/stores/auth-store';
import { buildCircularAttachmentUrl } from '../../utils/circular/attachmentUrl';

const UserNotifications = ({ currentUser }) => {
    const [userNotifications, setUserNotifications] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [sortCriteria, setSortCriteria] = useState('created_at'); // Default sort by date
    const [sortDirection, setSortDirection] = useState('desc'); // Default descending
    const [selectedComment, setSelectedComment] = useState(null); // For popup
    const navigate = useNavigate();

        // Get user data for header
    const { user } = useAuth();
    const userName = user?.display_name || user?.employee_id || user?.crew_id;

    // Logout handler
    const handleLogout = async () => {
        await useAuthStore.getState().logout();
        sessionStorage.clear();
        navigate('/login', { replace: true });
    };

    // --- Fetch User's Notifications ---
    const fetchUserNotifications = async (order = sortDirection, criteria = sortCriteria) => {
        if (!currentUser?.employee_id) {
            setUserNotifications([]);
            return;
        }

        setIsLoading(true);
        try {
            const queryParams = new URLSearchParams({
                created_by: currentUser.employee_id,
                sort_order: order,
            }).toString();

            const response = await fetch(`http://localhost:8000/api/circular/api/user-notifications/?${queryParams}`);
            if (!response.ok) {
                if (response.status === 404) {
                    console.warn("User notifications endpoint not found (404).");
                    setUserNotifications([]);
                    return;
                }
                throw new Error(`Failed to fetch notifications: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();

            // --- Client-side sorting ---
            let sortedData = [...data];
            if (criteria === 'created_at') {
                sortedData.sort((a, b) => {
                    const dateA = new Date(a.created_at);
                    const dateB = new Date(b.created_at);
                    return sortDirection === 'desc' ? dateB - dateA : dateA - dateB;
                });
            }

            setUserNotifications(sortedData);
        } catch (err) {
            console.error("Error fetching user notifications:", err);
            setUserNotifications([]);
        } finally {
            setIsLoading(false);
        }
    };

    // --- Handle Sort Criteria Change ---
    const handleSortCriteriaChange = (newCriteria) => {
        setSortCriteria(newCriteria);
    };

    // --- Handle Sort Direction Change ---
    const handleSortDirectionChange = (newDirection) => {
        setSortDirection(newDirection);
    };

    // --- Fetch on mount and when user changes ---
    useEffect(() => {
        fetchUserNotifications(sortDirection, sortCriteria);
    }, [currentUser?.employee_id, sortDirection, sortCriteria]); //Add sort dependencies

    // --- Utility function to get status badge ---
    const getStatusBadge = (status) => {
        const statusMap = {
            1: { text: 'Pending', color: 'bg-yellow-100 text-yellow-800' },
            2: { text: 'Approved', color: 'bg-green-100 text-green-800' },
            3: { text: 'Rejected', color: 'bg-red-100 text-red-800' },
        };
        const statusInfo = statusMap[status] || { text: 'Unknown', color: 'bg-gray-100 text-gray-800' };
        return (
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
                {statusInfo.text}
            </span>
        );
    };

    // --- Handle Supersede Click (NEW) ---
    const handleSupersedeClick = (notificationId) => {
        console.log("🚀 Supersede clicked for notification ID:", notificationId);

        // 1. Store the notification ID in localStorage
        localStorage.setItem('supersedingNotificationId', notificationId);
        console.log("✅ Stored supersedingNotificationId in localStorage:", notificationId);

        // 2. Navigate to the main create page
        // This will reload the page and trigger the Officeuser/Admin component to check localStorage
        navigate('/'); // Use navigate to go to the main page
    };
    // --- End Handle Supersede Click ---

    // --- Popup Handlers ---
    const handleCommentClick = (comment, isDeleted) => { // Accept isDeleted flag
        if (comment && !isDeleted) { // Only open popup if not deleted
            setSelectedComment(comment);
        } else if (isDeleted) {
            console.log("handleCommentClick: Notification is deleted, ignoring click.");
            // Optionally, you could show an alert: alert("This notification has been deleted.");
        }
    };

    const closeModal = () => {
        setSelectedComment(null);
    };

    return (
          
        <div className="max-w-7xl mx-auto p-4 bg-white rounded-xl shadow-sm">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">My Submissions</h1>
            </div>

            

            {/* --- Notifications List --- */}
            {isLoading ? (
                <div className="text-center py-10">
                    <p className="text-gray-500">Loading your notifications...</p>
                </div>
            ) : userNotifications.length > 0 ? (
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                    <table className="min-w-full divide-y divide-gray-300">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">ID / SR No</th>
                                {/* <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Type</th> */}
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Date</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Status</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Comment</th>
                                {/* <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Supersede</th> */}
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Download</th>
                            </tr>
                        </thead>

                        <tbody className="divide-y divide-gray-200 bg-white">
                            {userNotifications.map((notification) => {
                                // --- Determine if notification is deleted ---
                                const isDeleted = notification.is_deleted === true || notification.is_deleted === 1;
                                // --- END Determine ---

                                return (
                                    <tr
                                        key={notification.id}
                                        // --- Apply red background if deleted ---
                                        className={`${isDeleted ? 'bg-red-50 hover:bg-red-50' : 'hover:bg-gray-50'}`}
                                        // --- END Apply red background ---
                                    >
                                        <td className={`whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium ${isDeleted ? 'text-gray-400' : 'text-gray-900'} sm:pl-6`}>
                                            {/* --- NEW: Show "DELETED" label for deleted notifications --- */}
                                            {isDeleted && (
                                                <span className="inline-block mr-2 px-2 py-0.5 text-xs font-semibold rounded-full bg-red-600 text-white">
                                                    DELETED
                                                </span>
                                            )}
                                            {/* --- END NEW: Show "DELETED" label --- */}
                                            {notification.sr_no}
                                        </td>
                                        {/* <td className={`whitespace-nowrap px-3 py-4 text-sm ${isDeleted ? 'text-gray-400' : 'text-gray-500'}`}>
                                            {notification.msc_type}
                                        </td> */}
                                        <td className={`whitespace-nowrap px-3 py-4 text-sm ${isDeleted ? 'text-gray-400' : 'text-gray-500'}`}>
                                            {new Date(notification.created_at).toLocaleDateString()}
                                        </td>
                                        <td className={`whitespace-nowrap px-3 py-4 text-sm ${isDeleted ? 'text-gray-400' : 'text-gray-500'}`}>
                                            {isDeleted ? (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                                    Deleted
                                                </span>
                                            ) : (
                                                getStatusBadge(notification.publish_status)
                                            )}
                                        </td>

                                        {/*  Comment cell (clickable popup) - Disabled if deleted */}
                                        <td
                                            // --- Apply greyed-out text and disabled cursor if deleted ---
                                            className={`px-3 py-4 text-sm max-w-xs ${
                                                isDeleted
                                                    ? 'text-gray-400 cursor-not-allowed'
                                                    : 'text-gray-500 cursor-pointer hover:text-indigo-600'
                                            }`}
                                            // --- END Apply styles ---
                                            onClick={() => handleCommentClick(notification.publish_comment, isDeleted)}
                                            title={isDeleted ? "Notification deleted" : "Click to view full comment"}
                                        >
                                            <div className="line-clamp-2">
                                                {notification.publish_comment || '—'}
                                            </div>
                                        </td>

                                        {/* Download column - Disabled if deleted */}
                                        <td className={`whitespace-nowrap px-3 py-4 text-sm ${isDeleted ? 'text-gray-400' : 'text-gray-500'}`}>
                                            {isDeleted ? (
                                                <span className="text-gray-400 italic">-</span> // Show dash or placeholder if deleted
                                            ) : (
                                                notification.attachment_url ? (
                                                    <a
                                                        href={buildCircularAttachmentUrl(notification.attachment_url)}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-indigo-100 hover:bg-indigo-200 text-indigo-700 shadow-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-400"
                                                        title="View Attachment"
                                                    >
                                                        {/* SVG Icon (Download / View) */}
                                                        <svg
                                                            xmlns="http://www.w3.org/2000/svg"
                                                            fill="none"
                                                            viewBox="0 0 24 24"
                                                            strokeWidth={2}
                                                            stroke="currentColor"
                                                            className="w-5 h-5"
                                                        >
                                                            <path
                                                                strokeLinecap="round"
                                                                strokeLinejoin="round"
                                                                d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4"
                                                            />
                                                        </svg>
                                                    </a>
                                                ) : (
                                                    <span className="text-gray-400 italic">No attachment</span>
                                                )
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="text-center py-10">
                    <p className="text-gray-500">You have no notifications yet.</p>
                </div>
            )}

            {/* Comment Popup Modal */}
            {selectedComment && (
                <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-lg p-6 max-w-lg w-full mx-4">
                        <h2 className="text-lg font-semibold mb-4 text-gray-800">Full Comment</h2>
                        <p className="text-gray-700 whitespace-pre-wrap">{selectedComment}</p>
                        <div className="mt-6 text-right">
                            <button
                                onClick={closeModal}
                                className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 focus:outline-none"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
      
    );
};

export default UserNotifications;
