// src/components/DraftNotifications.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PageLayout from '../../components/layout/PageLayout';
import { useAuth } from '../../hooks/auth/useAuth';
import { useAuthStore } from '@/stores/auth-store';
import { buildCircularAttachmentUrl } from '../../utils/circular/attachmentUrl';

const DraftNotifications = ({ currentUser }) => {

    

    const [draftNotifications, setDraftNotifications] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [sortCriteria, setSortCriteria] = useState('created_at'); // Default sort by date
    const [sortDirection, setSortDirection] = useState('desc'); // Default descending
    const [selectedComment, setSelectedComment] = useState(null); // For popup
    const navigate = useNavigate(); // Ensure you have this hook initialized
    // const currentUser = JSON.parse(localStorage.getItem('user')); // Get current user info
    const isAdmin = currentUser?.role_name?.toLowerCase() === 'admin'; // Determine role
    const [typeToIdMap, setTypeToIdMap] = useState({});
    const [idToTypeMap, setIdToTypeMap] = useState({}); // This is the variable causing the error
    const [priorityToIdMap, setPriorityToIdMap] = useState({});
    const [idToPriorityMap, setIdToPriorityMap] = useState({});
    const [deptToIdMap, setDeptToIdMap] = useState({});
    const [idToDeptMap, setIdToDeptMap] = useState({});
    const [subCategories, setSubCategories] = useState([]);
    const [idToSubCatMap, setIdToSubCatMap] = useState({});
    const [secondSubCategories, setSecondSubCategories] = useState([]);
    const [idToSecondSubCatMap, setIdToSecondSubCatMap] = useState({});

        // Get user data for header
    
    const { user } = useAuth();
    const userName = user?.display_name || user?.employee_id || user?.crew_id;

    // Logout handler
    const handleLogout = async () => {
        await useAuthStore.getState().logout();
        sessionStorage.clear();
        navigate('/login', { replace: true });
    };


    // --- Fetch User's Draft Notifications ---
    const fetchUserDrafts = async (order = sortDirection, criteria = sortCriteria) => {
        console.log("=== fetchUserDrafts: Starting function ===");
        console.log("fetchUserDrafts: Current user:", currentUser);

        if (!currentUser?.employee_id) {
            console.log("fetchUserDrafts: No user found, setting empty array");
            setDraftNotifications([]);
            return;
        }

        setIsLoading(true);
        try {
            const queryParams = new URLSearchParams({
                created_by: currentUser.employee_id,
                sort_order: order,
            }).toString();

            console.log("fetchUserDrafts: Query params:", queryParams);

            const response = await fetch(`http://localhost:8000/api/circular/api/user-drafts/?${queryParams}`);
            console.log("fetchUserDrafts: Response status:", response.status);

            if (!response.ok) {
                if (response.status === 404) {
                    console.warn("fetchUserDrafts: User drafts endpoint not found (404).");
                    setDraftNotifications([]);
                    return;
                }
                throw new Error(`Failed to fetch draft notifications: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            console.log("fetchUserDrafts: Received ", data);

            // --- Client-side sorting ---
            let sortedData = [...data];
            if (criteria === 'created_at') {
                sortedData.sort((a, b) => {
                    const dateA = new Date(a.created_at);
                    const dateB = new Date(b.created_at);
                    const result = sortDirection === 'desc' ? dateB - dateA : dateA - dateB;
                    console.log(`fetchUserDrafts: Sorting comparison: ${dateA} vs ${dateB} = ${result}`);
                    return result;
                });
            }

            setDraftNotifications(sortedData);
            console.log("fetchUserDrafts: Set draft notifications, count:", sortedData.length);
        } catch (err) {
            console.error("fetchUserDrafts: Error fetching user drafts:", err);
            setDraftNotifications([]);
        } finally {
            setIsLoading(false);
            console.log("fetchUserDrafts: Loading finished");
        }
    };


      // --- Fetch Options and Create Maps ---
    useEffect(() => {
        const fetchOptions = async () => {
            try {
                // Fetch document types
                const docRes = await fetch('http://localhost:8000/api/circular/api/document-types/');
                const docData = await docRes.json();
                const docTypeMap = {};
                const docIdToNameMap = {};
                if (Array.isArray(docData)) {
                    docData.forEach(item => {
                        if (item && item[0] && item[1]) { // Assuming [uuid, name]
                            docTypeMap[item[1]] = item[0]; // name -> id
                            docIdToNameMap[item[0]] = item[1]; // id -> name
                        }
                    });
                }
                setTypeToIdMap(docTypeMap);
                setIdToTypeMap(docIdToNameMap); // Populate idToTypeMap here

                // Fetch priorities
                const prioRes = await fetch('http://localhost:8000/api/circular/api/priorities/');
                const prioData = await prioRes.json();
                const prioMap = {};
                const prioIdToNameMap = {};
                if (Array.isArray(prioData)) {
                    prioData.forEach(item => {
                        if (item && item[0] && item[1]) { // Assuming [uuid, name]
                            prioMap[item[1]] = item[0]; // name -> id
                            prioIdToNameMap[item[0]] = item[1]; // id -> name
                        }
                    });
                }
                setPriorityToIdMap(prioMap);
                setIdToPriorityMap(prioIdToNameMap); //  Populate idToPriorityMap here

                // Fetch departments
                const deptRes = await fetch('http://localhost:8000/api/circular/api/departments/');
                const deptData = await deptRes.json();
                const deptMap = {};
                const deptIdToNameMap = {};
                if (Array.isArray(deptData)) {
                    deptData.forEach(item => {
                        if (item && item[0] && item[1]) { // Assuming [uuid, name]
                            deptMap[item[1]] = item[0]; // name -> id
                            deptIdToNameMap[item[0]] = item[1]; // id -> name
                        }
                    });
                }
                setDeptToIdMap(deptMap);
                setIdToDeptMap(deptIdToNameMap); //  Populate idToDeptMap here

                // Fetch sub-categories
                const subCatRes = await fetch('http://localhost:8000/api/circular/api/sub-categories/');
                const subCatData = await subCatRes.json();
                const subCatIdToNameMap = {};
                if (Array.isArray(subCatData)) {
                    subCatData.forEach(item => {
                        if (item && item.id && item.name) {
                            subCatIdToNameMap[item.id] = item.name; // id -> name
                        }
                    });
                }
                setSubCategories(subCatData);
                setIdToSubCatMap(subCatIdToNameMap); // âœ… Populate idToSubCatMap here

                // Fetch second sub-categories (example - adjust as needed)
                const secondSubCatRes = await fetch('http://localhost:8000/api/circular/api/second-sub-categories/');
                const secondSubCatData = await secondSubCatRes.json();
                const secondSubCatIdToNameMap = {};
                if (Array.isArray(secondSubCatData)) {
                    secondSubCatData.forEach(item => {
                        if (item && item.id && item.name) {
                            secondSubCatIdToNameMap[item.id] = item.name; // id -> name
                        }
                    });
                }
                setSecondSubCategories(secondSubCatData);
                setIdToSecondSubCatMap(secondSubCatIdToNameMap); //  Populate idToSecondSubCatMap here

            } catch (err) {
                console.error('Failed to fetch options:', err);
            }
        };

        fetchOptions();
    }, []); // Run once on mount


    // --- Handle Sort Criteria Change ---
    const handleSortCriteriaChange = (newCriteria) => {
        console.log("handleSortCriteriaChange: New criteria:", newCriteria);
        setSortCriteria(newCriteria);
    };

    // --- Handle Sort Direction Change ---
    const handleSortDirectionChange = (newDirection) => {
        console.log("handleSortDirectionChange: New direction:", newDirection);
        setSortDirection(newDirection);
    };

    // --- Fetch on mount and when user changes ---
    useEffect(() => {
        console.log("=== DraftNotifications useEffect: Running ===");
        console.log("Current user:", currentUser?.employee_id);
        fetchUserDrafts(sortDirection, sortCriteria);
    }, [currentUser?.employee_id, sortDirection, sortCriteria]);


    // --- NEW: Define handleEditClick INSIDE the component ---

    const handleEditClick = async (notificationId) => {
        console.log("ðŸš€ handleEditClick: Edit clicked for notification ID (SR No):", notificationId);

        try {
            const primaryDashboardPath = isAdmin ? '/circular/admin' : '/circular/office';
            const draftEditUrl = `${primaryDashboardPath}?draft_sr_no=${encodeURIComponent(notificationId)}`;
            console.log(`handleEditClick: Navigating to draft edit URL: ${draftEditUrl}`);
            navigate(draftEditUrl);
        } catch (error) {
            console.error("handleEditClick: Error fetching or processing draft ", error);
            alert(`Failed to load draft: ${error.message}`);
        }
    };
    // --- END NEW ---



    // --- Handle Delete Click ---
    const handleDeleteClick = async (draftId, srNo, displaySrNo) => {
        console.log("ðŸš€ handleDeleteClick: Delete clicked for draft ID:", draftId, "SR No:", srNo, "Display SR No:", displaySrNo);

        const confirmed = window.confirm(`Are you sure you want to delete draft notification ${displaySrNo}?`);
        console.log("handleDeleteClick: User confirmed:", confirmed);

        if (!confirmed) {
            console.log("handleDeleteClick: User cancelled deletion");
            return;
        }

        try {
            console.log("handleDeleteClick: Sending delete request for draft ID:", draftId);
            const response = await fetch(`http://localhost:8000/api/circular/api/drafts/${draftId}/delete/`, {
                method: 'POST', // Using POST to avoid browser compatibility issues
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            console.log("handleDeleteClick: Delete response status:", response.status);

            if (response.ok) {
                const result = await response.json();
                console.log("handleDeleteClick: Delete response ", result);

                // Remove the deleted notification from the local state
                setDraftNotifications(prev => {
                    const newDrafts = prev.filter(notification => notification.id !== draftId);
                    console.log("handleDeleteClick: Removed notification from state, new count:", newDrafts.length);
                    return newDrafts;
                });

                console.log("handleDeleteClick: Notification soft-deleted successfully");
                alert("Draft deleted successfully");
            } else {
                const result = await response.json();
                console.error("handleDeleteClick: Delete failed with error:", result.error);
                throw new Error(result.error || `Failed to delete notification: ${response.status} ${response.statusText}`);
            }
        } catch (err) {
            console.error("handleDeleteClick: Error deleting notification:", err);
            alert(`Failed to delete draft: ${err.message}`);
        }
    };

    // --- Utility function to get status badge ---
    const getStatusBadge = (status) => {
        console.log("getStatusBadge: Status received:", status);
        const statusMap = {
            0: { text: 'Draft', color: 'bg-gray-100 text-gray-800' },
            1: { text: 'Pending', color: 'bg-yellow-100 text-yellow-800' },
            2: { text: 'Approved', color: 'bg-green-100 text-green-800' },
            3: { text: 'Rejected', color: 'bg-red-100 text-red-800' },
        };
        const statusInfo = statusMap[status] || { text: 'Unknown', color: 'bg-gray-100 text-gray-800' };
        console.log("getStatusBadge: Returning badge:", statusInfo);
        return (
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
                {statusInfo.text}
            </span>
        );
    };

    // --- Popup Handlers ---
    const handleCommentClick = (comment) => {
        console.log("handleCommentClick: Comment clicked:", comment);
        if (comment) setSelectedComment(comment);
    };

    const closeModal = () => {
        console.log("closeModal: Closing comment modal");
        setSelectedComment(null);
    };

    console.log("=== DraftNotifications: Rendering ===");
    console.log("Current draft count:", draftNotifications.length);
    console.log("Current user:", currentUser?.employee_id);

    return (
         
        <div className="max-w-7xl mx-auto p-4 bg-white rounded-xl shadow-sm">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">My Draft Notifications</h1>
                <span className="text-sm text-gray-500">({draftNotifications.length} drafts)</span>
            </div>

            {/* --- Sorting Controls --- */}
            <div className="mb-6 p-4 bg-gray-50 rounded-lg flex flex-wrap items-center gap-4">
                <div>
                    <label htmlFor="sortCriteria" className="block text-sm font-medium text-gray-700 mb-1">
                        Sort by:
                    </label>
                    <select
                        id="sortCriteria"
                        value={sortCriteria}
                        onChange={(e) => handleSortCriteriaChange(e.target.value)}
                        className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    >
                        <option value="created_at">Date Created</option>
                        <option value="sr_no">Serial Number</option>
                        {/* <option value="msc_type">Type</option> */}
                        <option value="dept">Department</option>
                        <option value="priority">Priority</option>
                    </select>
                </div>
                <div>
                    <label htmlFor="sortDirection" className="block text-sm font-medium text-gray-700 mb-1">
                        Order:
                    </label>
                    <select
                        id="sortDirection"
                        value={sortDirection}
                        onChange={(e) => handleSortDirectionChange(e.target.value)}
                        className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    >
                        <option value="desc">Descending</option>
                        <option value="asc">Ascending</option>
                    </select>
                </div>
            </div>

            {/* --- Draft Notifications List --- */}
            {isLoading ? (
                <div className="text-center py-10">
                    <p className="text-gray-500">Loading your draft notifications...</p>
                </div>
            ) : draftNotifications.length > 0 ? (
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                    <table className="min-w-full divide-y divide-gray-300">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">ID / SR No</th>
                                {/* <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Type</th> */}
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Date</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Status</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Comment</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Actions</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Download</th>
                            </tr>
                        </thead>

                        <tbody className="divide-y divide-gray-200 bg-white">
                            {draftNotifications.map((notification) => (
                                <tr key={notification.id} className="hover:bg-gray-50">
                                    <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                                        {notification.sr_no}
                                    </td>
                                    {/* <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                                        {notification.msc_type}
                                    </td> */}
                                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                                        {new Date(notification.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                                        {getStatusBadge(notification.publish_status)}
                                    </td>

                                    {/* Comment cell (clickable popup) */}
                                    <td
                                        className="px-3 py-4 text-sm text-gray-500 max-w-xs cursor-pointer hover:text-indigo-600"
                                        onClick={() => handleCommentClick(notification.publish_comment)}
                                        title="Click to view full comment"
                                    >
                                        <div className="line-clamp-2">
                                            {notification.publish_comment || 'â€”'}
                                        </div>
                                    </td>

                                    {/* Actions column */}
                                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => handleEditClick(notification.sr_no)}
                                                className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md shadow-sm text-indigo-800 bg-indigo-200 hover:bg-indigo-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-400"
                                            >
                                                Edit
                                            </button>
                                            <button
                                                onClick={() => handleDeleteClick(notification.id, notification.sr_no, notification.sr_no)}
                                                className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md shadow-sm text-red-800 bg-red-200 hover:bg-red-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-400"
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </td>

                                    {/* Download column */}
                                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                                        {notification.attachment_url ? (
                                            <a
                                                href={buildCircularAttachmentUrl(notification.attachment_url)}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md shadow-sm text-indigo-800 bg-indigo-200 hover:bg-indigo-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-400"
                                            >
                                                Download
                                            </a>
                                        ) : (
                                            <span className="text-gray-400 italic">No attachment</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="text-center py-10">
                    <p className="text-gray-500">You have no draft notifications.</p>
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

export default DraftNotifications;
