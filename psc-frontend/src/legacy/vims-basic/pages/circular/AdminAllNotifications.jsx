// src/components/AdminAllNotifications.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'; // For back button if needed
import PageLayout from '../../components/layout/PageLayout';
import { useAuth } from '../../hooks/auth/useAuth';
import { useAuthStore } from '@/stores/auth-store';
import { buildCircularAttachmentUrl } from '../../utils/circular/attachmentUrl';

const AdminAllNotifications = () => {
    const [allNotifications, setAllNotifications] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [sortCriteria, setSortCriteria] = useState('created_at'); // Default sort by date
    const [sortDirection, setSortDirection] = useState('desc'); // Default descending
    const [publishStatusFilter, setPublishStatusFilter] = useState(null); // null = all
    const [selectedComment, setSelectedComment] = useState(null); // Popup state
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

    // --- Fetch All Notifications ---
    const fetchAllNotifications = async (criteria = sortCriteria, direction = sortDirection, publishStatus = publishStatusFilter) => {
        setIsLoading(true);
        try {
            const params = {
                sort_by: criteria,
                sort_order: direction,
            };

            if (publishStatus !== null) {
                if (Array.isArray(publishStatus)) {
                    params.publish_status__in = publishStatus.join(',');
                } else {
                    params.publish_status = publishStatus;
                }
            }

            const queryParams = new URLSearchParams(params).toString();
            const response = await fetch(`http://localhost:8001/api/circular/api/submitted/?${queryParams}`);

            if (!response.ok) {
                if (response.status === 404) {
                    console.warn("Notifications endpoint not found (404).");
                    setAllNotifications([]);
                    return;
                }
                throw new Error(`Failed to fetch notifications: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            setAllNotifications(data);
            console.log("Fetched all notifications for admin:", data);
        } catch (err) {
            console.error("Error fetching all notifications:", err);
            setAllNotifications([]);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchAllNotifications();
    }, []);

    // --- Sorting / Filtering Handlers ---
    const handleSortCriteriaChange = (newCriteria) => {
        setSortCriteria(newCriteria);
        fetchAllNotifications(newCriteria, sortDirection, publishStatusFilter);
    };

    const handleSortDirectionChange = (newDirection) => {
        setSortDirection(newDirection);
        fetchAllNotifications(sortCriteria, newDirection, publishStatusFilter);
    };

    const handleStatusFilterChange = (newFilter) => {
        setPublishStatusFilter(newFilter);
        fetchAllNotifications(sortCriteria, sortDirection, newFilter);
    };

    // --- CSV Download ---
    const handleDownload = () => {
        if (allNotifications.length === 0) {
            alert('No data to download');
            return;
        }

        const headers = Object.keys(allNotifications[0]).join(',');
        const rows = allNotifications.map(notification =>
            Object.values(notification).map(value =>
                `"${String(value).replace(/"/g, '""')}"`
            ).join(',')
        ).join('\n');

        const csvContent = `data:text/csv;charset=utf-8,${headers}\n${rows}`;
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', 'notifications.csv');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // --- Status Badge ---
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

    // --- Popup Handlers ---
    const handleCommentClick = (comment) => {
        if (comment) setSelectedComment(comment);
    };
    const closeModal = () => setSelectedComment(null);

    return (
         
        <div className="max-w-7xl mx-auto p-4 bg-white rounded-xl shadow-sm">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">All Notifications</h1>
            </div>

            {/* --- Controls --- */}
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
                        <option value="msc_type">Type</option>
                        <option value="publish_status">Status</option>
                        <option value="created_by">Created By</option>
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

                <div>
                    <label htmlFor="publishStatusFilter" className="block text-sm font-medium text-gray-700 mb-1">
                        Filter by Status:
                    </label>
                    <select
                        id="publishStatusFilter"
                        value={
                            publishStatusFilter === null ? 'all' :
                                publishStatusFilter.length === 2 ? 'approved_rejected' :
                                    publishStatusFilter[0] === 2 ? 'approved' : 'rejected'
                        }
                        onChange={(e) => {
                            const val = e.target.value;
                            let filter = null;
                            if (val === 'approved') filter = [2];
                            else if (val === 'rejected') filter = [3];
                            else if (val === 'approved_rejected') filter = [2, 3];
                            handleStatusFilterChange(filter);
                        }}
                        className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    >
                        <option value="all">All Notifications</option>
                        <option value="approved_rejected">Approved & Rejected</option>
                        <option value="approved">Approved Only</option>
                        <option value="rejected">Rejected Only</option>
                    </select>
                </div>
            </div>

            {/* --- Notifications Table --- */}
            {isLoading ? (
                <div className="text-center py-10">
                    <p className="text-gray-500">Loading all notifications...</p>
                </div>
            ) : allNotifications.length > 0 ? (
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                    <table className="min-w-full divide-y divide-gray-300">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">ID / SR No</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Type</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Created By</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Date</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Status</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Comment</th>
                                <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Download</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                            {allNotifications.map((n) => (
                                <tr key={n.id} className="hover:bg-gray-50">
                                    <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">{n.sr_no}</td>
                                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{n.msc_type}</td>
                                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{n.created_by}</td>
                                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{new Date(n.created_at).toLocaleDateString()}</td>
                                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{getStatusBadge(n.publish_status)}</td>

                                    {/* âœ… Comment (clickable popup) */}
                                    <td
                                        className="px-3 py-4 text-sm text-gray-500 max-w-xs cursor-pointer hover:text-indigo-600"
                                        onClick={() => handleCommentClick(n.publish_comment)}
                                        title="Click to view full comment"
                                    >
                                        <div className="line-clamp-2">{n.publish_comment || 'â€”'}</div>
                                    </td>

                                    {/* Download */}
                                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                                        {n.attachment_url ? (
                                            <a
                                                href={buildCircularAttachmentUrl(n.attachment_url)}
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
                    <p className="text-gray-500">No notifications found.</p>
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

export default AdminAllNotifications;
