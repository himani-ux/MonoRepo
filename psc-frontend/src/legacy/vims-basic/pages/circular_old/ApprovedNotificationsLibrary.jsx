// src/components/ApprovedNotificationsLibrary.jsx
import React, { useState, useEffect } from "react";
import {
    ArrowDownUp,
    Filter,
    RefreshCcw,
    FileDown,
    Printer,
    Bell,
    Circle,
    Search,
    Trash2,
    RotateCcw,
    Eye
} from "lucide-react";
import { Download as DownloadIcon } from 'lucide-react';
import { WithPermission } from '../../utils/circular/permissionUtils';
import { useAuth } from '../../hooks/auth/useAuth';
import { buildCircularAttachmentUrl } from '../../utils/circular/attachmentUrl';
import { parseCircularStoredArray } from '../../utils/circular/supersede';



const ApprovedNotificationsLibrary = () => {

    const { user } = useAuth();
    const [notifications, setNotifications] = useState([]);
    const [filteredNotifications, setFilteredNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [viewingSeenCrews, setViewingSeenCrews] = useState(null); // Store the SR No of the notification to view seen crews for
    const [seenCrewsData, setSeenCrewsData] = useState([]); // Store the fetched crew data
    const [loadingSeenCrews, setLoadingSeenCrews] = useState(false); // Track loading state

    // Filters
    const [selectedType, setSelectedType] = useState("all");
    const [selectedPriority, setSelectedPriority] = useState("all");
    const [sortCriteria, setSortCriteria] = useState("created_at");
    const [sortDirection, setSortDirection] = useState("desc");
    const [searchQuery, setSearchQuery] = useState("");
    const [sendingIndividualReminder, setSendingIndividualReminder] = useState(null); // Store the crew_id being processed for individual reminder
    const [typeUuidToNameMap, setTypeUuidToNameMap] = useState({});
    const [priorityUuidToNameMap, setPriorityUuidToNameMap] = useState({});
    const [loadingLookupMaps, setLoadingLookupMaps] = useState(true); // To track loading of lookup data

    const normalizeCircularTypeToken = (value) => {
        return String(value ?? "")
            .toLowerCase()
            .replace(/[^a-z0-9]/g, "");
    };

  


    // --- NEW: Fetch Lookup Maps on Component Mount ---
    useEffect(() => {
        const fetchLookupMaps = async () => {
            // console.log("ApprovedNotificationsLibrary: Fetching lookup maps (type, priority)...");
            try {
                // Fetch Document Types
                const typeRes = await fetch('http://localhost:8001/api/circular/api/document-types/');
                if (!typeRes.ok) {
                    throw new Error(`Failed to fetch document types: ${typeRes.status} ${typeRes.statusText}`);
                }
                const typeData = await typeRes.json();
                // console.log("ApprovedNotificationsLibrary: Fetched document types:", typeData);

                // Build type UUID to name map
                const typeMap = {};
                if (Array.isArray(typeData)) {
                    typeData.forEach(item => {
                        // Check if item is an array with at least 2 elements
                        if (Array.isArray(item) && item.length >= 2) {
                            const uuid = item[0]; // First element is the UUID
                            const name = item[1]; // Second element is the name
                            if (uuid && name) {
                                typeMap[uuid] = name;
                            }
                        }
                    });
                }
                setTypeUuidToNameMap(typeMap);
                // console.log("ApprovedNotificationsLibrary: Built type UUID to name map:", typeMap);

                // Fetch Priorities
                const priorityRes = await fetch('http://localhost:8001/api/circular/api/priorities/');
                if (!priorityRes.ok) {
                    throw new Error(`Failed to fetch priorities: ${priorityRes.status} ${priorityRes.statusText}`);
                }
                const priorityData = await priorityRes.json();
                // console.log("ApprovedNotificationsLibrary: Fetched priorities:", priorityData);

                // Build priority UUID to name map
                const priorityMap = {};
                if (Array.isArray(priorityData)) {
                    priorityData.forEach(item => {
                        // Check if item is an array with at least 2 elements
                        if (Array.isArray(item) && item.length >= 2) {
                            const uuid = item[0]; // First element is the UUID
                            const name = item[1]; // Second element is the name
                            if (uuid && name) {
                                priorityMap[uuid] = name;
                            }
                        }
                    });
                }
                setPriorityUuidToNameMap(priorityMap);
                // console.log("ApprovedNotificationsLibrary: Built priority UUID to name map:", priorityMap);

                setLoadingLookupMaps(false); // Stop loading lookup maps
                // console.log("ApprovedNotificationsLibrary: Finished fetching lookup maps.");

            } catch (err) {
                // console.error("ApprovedNotificationsLibrary: Error fetching lookup maps:", err);
                setError(`Failed to load lookup data: ${err.message}`); // Set error state
                setLoadingLookupMaps(false); // Stop loading even if there's an error
            }
        };

        fetchLookupMaps(); // Call the function


    }, []);


    useEffect(() => {
        if (loadingLookupMaps) {
            console.log("ApprovedNotificationsLibrary: Waiting for lookup maps to load before fetching notifications.");
            return;
        }

        if (error) {
            console.log("ApprovedNotificationsLibrary: Lookup maps failed to load, skipping notification fetch.");
            // return;
        }

        const fetchApprovedNotifications = async () => {
            try {
                setLoading(true);
                // console.log("ApprovedNotificationsLibrary: Fetching approved notifications...");
                const response = await fetch(
                    "http://localhost:8001/api/circular/api/approved-notifications/"
                );
                if (!response.ok) {
                    throw new Error(`Failed to fetch notifications: ${response.status} ${response.statusText}`);
                }
                const data = await response.json();
                // console.log("ApprovedNotificationsLibrary: Fetched raw notifications ", data);

                const notificationsWithNames = data.map(notification => ({
                    ...notification,
                    msc_type: typeUuidToNameMap[notification.msc_type] || notification.msc_type,
                    priority: priorityUuidToNameMap[notification.priority] || notification.priority,
                }));
                // console.log("ApprovedNotificationsLibrary: Mapped notifications data with names:", notificationsWithNames);

                setNotifications(notificationsWithNames);
                setFilteredNotifications(notificationsWithNames);
            } catch (err) {
                // console.error("ApprovedNotificationsLibrary: Error fetching notifications:", err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchApprovedNotifications();
    }, [loadingLookupMaps, error]);




    useEffect(() => {
        let result = [...notifications];


        if (searchQuery.trim() !== "") {
            const query = searchQuery.trim().toLowerCase();
            result = result.filter((n) =>
                (n.title && n.title.toLowerCase().includes(query)) ||
                (n.sr_no && n.sr_no.toLowerCase().includes(query)) ||
                (n.hashtags && n.hashtags.toLowerCase().includes(query))
            );
        }

        // Type filter
        if (selectedType !== "all") {
            const selectedTypeToken = normalizeCircularTypeToken(selectedType);
            result = result.filter(
                (n) => normalizeCircularTypeToken(n.msc_type) === selectedTypeToken
            );
        }

        // Priority filter
        if (selectedPriority !== "all") {
            result = result.filter((n) => n.priority === selectedPriority);
        }

        // Sorting
        if (sortCriteria === "created_at") {
            result.sort((a, b) =>
                sortDirection === "desc"
                    ? new Date(b.created_at) - new Date(a.created_at)
                    : new Date(a.created_at) - new Date(b.created_at)
            );
        } else if (sortCriteria === "sr_no") {
            result.sort((a, b) =>
                sortDirection === "desc"
                    ? (b.sr_no || "").localeCompare(a.sr_no || "")
                    : (a.sr_no || "").localeCompare(b.sr_no || "")
            );
        }

        setFilteredNotifications(result);
    }, [
        notifications,
        selectedType,
        selectedPriority,
        sortCriteria,
        sortDirection,
        searchQuery,
    ]);


    const resetFilters = () => {
        setSelectedType("all");
        setSelectedPriority("all");
        setSortCriteria("created_at");
        setSortDirection("desc");
        setSearchQuery("");
    };

    const getTypeBadge = (typeInput) => {
        // The typeInput should now be the name string thanks to the mapping in Step 3
        const type = typeInput; // It's already the name

        // Normalize type for safer comparison and mapping
        const normalizedType = normalizeCircularTypeToken(type);
        const map = {
            alert: "bg-red-100 text-red-700",
            circular: "bg-blue-100 text-blue-700",
            workinstruction: "bg-amber-100 text-amber-700",
        };
        const style = map[normalizedType] || "bg-gray-100 text-gray-700";
        const displayMap = {
            alert: "Alert",
            circular: "Circular",
            workinstruction: "Work Instruction",
        };
        const displayText = displayMap[normalizedType] || String(type || "")
            .replace(/[_-]+/g, " ")
            .replace(/\s+/g, " ")
            .trim()
            .split(" ")
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');

        return (
            <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${style}`}
            >
                {displayText || 'Unknown Type'}
            </span>
        );
    };


    // --- NEW: Handler for Send Reminder Button ---
    const handleSendReminder = async (srNoForReminder) => {
        console.log("ðŸ”” handleSendReminder: Sending reminder for notification SR No:", srNoForReminder);
        const confirmed = window.confirm(`Are you sure you want to send a reminder for notification ${srNoForReminder}?`);
        if (!confirmed) {
            console.log("handleSendReminder: User cancelled reminder.");
            return; // Stop if user cancels
        }

        try {
            // Call the backend endpoint to update the reminder_sent_at field
            const response = await fetch(`http://localhost:8001/api/circular/api/notifications/${srNoForReminder}/send-reminder/`, { // Use your new reminder endpoint
                method: 'POST', // Use POST for state-changing actions
                headers: {
                    'Content-Type': 'application/json',
                    // 'X-CSRFToken': getCookie('csrftoken'), // Add if needed
                },
                // credentials: 'include' // Include if using sessions/cookies for auth
            });

            const result = await response.json();

            if (response.ok) {
                console.log("âœ… handleSendReminder: Reminder sent successfully for notification", srNoForReminder);
                alert(`Reminder sent successfully for notification ${srNoForReminder}.`);
                // Optionally, you could refresh the list here if needed to reflect the updated reminder timestamp
                // fetchUserNotifications(sortDirection, sortCriteria);
            } else {
                console.error("handleSendReminder: Error sending reminder:", result.error);
                alert(`Error sending reminder: ${result.error || 'Unknown error'}`);
            }
        } catch (err) {
            console.error("handleSendReminder: Network error sending reminder for notification", srNoForReminder, err);
            alert('Network error occurred while sending reminder.');
        }
    };
    // --- END NEW ---



    // --- NEW: Handler for View Seen Crews Button ---
    const handleViewSeenCrews = async (notificationSrNo) => { // Accept the SR No string
        console.log("ðŸš€ handleViewSeenCrews: Fetching seen crews for notification SR No:", notificationSrNo);
        setViewingSeenCrews(notificationSrNo); // Set the SR No to view
        setLoadingSeenCrews(true); // Start loading

        try {
            const response = await fetch(`http://localhost:8001/api/circular/api/notifications/${notificationSrNo}/crew-delivery-status/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            const result = await response.json();

            if (response.ok) {
                console.log("âœ… handleViewSeenCrews: Successfully fetched delivery records for notification", notificationSrNo);
                setSeenCrewsData(result.delivery_records || []); // Store the data (ensure it's an array)
                setLoadingSeenCrews(false); // Stop loading
            } else {
                console.error("handleViewSeenCrews: Failed to fetch delivery records for notification", notificationSrNo, result.error);
                alert(`Error fetching seen crews: ${result.error || 'Unknown error'}`);
                setViewingSeenCrews(null); // Clear the viewing state on error
                setSeenCrewsData([]); // Clear previous data
                setLoadingSeenCrews(false); // Stop loading
            }
        } catch (err) {
            console.error("handleViewSeenCrews: Network error fetching seen crews for notification", notificationSrNo, err);
            alert('Network error occurred while fetching seen crews.');
            setViewingSeenCrews(null); // Clear the viewing state on error
            setSeenCrewsData([]); // Clear previous data
            setLoadingSeenCrews(false); // Stop loading
        }
    };
    // --- END NEW ---


    // --- NEW: Handler for Send Individual Reminder Button ---
    const handleSendIndividualReminder = async (notificationSrNo, crewId) => {
        console.log(`ðŸ”” handleSendIndividualReminder: Sending individual reminder for notification ${notificationSrNo} to crew ${crewId}`);
        const confirmed = window.confirm(`Are you sure you want to send a reminder to crew ${crewId} for notification ${notificationSrNo}?`);
        if (!confirmed) {
            console.log("handleSendIndividualReminder: User cancelled individual reminder.");
            return; // Stop if user cancels
        }

        // Set loading state for this specific crew
        setSendingIndividualReminder(crewId);

        try {
            // Call the backend endpoint to update the reminder_sent_at field for this specific crew and notification
            const response = await fetch(`http://localhost:8001/api/circular/api/notifications/${notificationSrNo}/send-individual-reminder/`, { // Use your new endpoint
                method: 'POST', // Use POST for state-changing actions
                headers: {
                    'Content-Type': 'application/json',
                    // 'X-CSRFToken': getCookie('csrftoken'), // Add if needed
                },
                body: JSON.stringify({ crew_id: crewId }), // Send the crew_id in the request body
                // credentials: 'include' // Include if using sessions/cookies for auth
            });

            const result = await response.json();

            if (response.ok) {
                console.log("âœ… handleSendIndividualReminder: Individual reminder sent successfully for crew", crewId);
                alert(`Reminder sent successfully to crew ${crewId}.`);
                // window.location.reload();

                // Optional: Refresh the list of seen crews to reflect the updated reminder status
                // This is optional because the UI will update when the modal re-renders after the state change
                // But you could trigger it manually if needed.
                // handleViewSeenCrews(notificationSrNo); // Re-fetch the data

            } else {
                console.error("handleSendIndividualReminder: Error sending individual reminder:", result.error);
                alert(`Error sending individual reminder: ${result.error || 'Unknown error'}`);
            }
        } catch (err) {
            console.error("handleSendIndividualReminder: Network error sending individual reminder for crew", crewId, err);
            alert('Network error occurred while sending individual reminder.');
        } finally {
            // Clear the loading state for this crew
            setSendingIndividualReminder(null);
        }
    };
    // --- END NEW ---



    // --- NEW: Handler for Delete Button (with Role-Based Check) ---

     const handleDelete = async (srNoToDelete) => {
        console.log(`ðŸš€ handleDelete: Attempting to delete notification ${srNoToDelete}`);

        // --- REMOVED: Admin Role Check ---
        // Any user can now attempt to delete
        // --- END REMOVED: Admin Role Check ---

        const confirmed = window.confirm(`Are you sure you want to delete notification ${srNoToDelete}? This action cannot be undone.`);
        if (!confirmed) {
            console.log("handleDelete: User cancelled deletion.");
            return;
        }

        try {
            const response = await fetch(`http://localhost:8001/api/circular/api/notifications/${srNoToDelete}/delete/`, {
                method: 'POST', // Use POST for state-changing actions
                headers: {
                    'Content-Type': 'application/json',
                    // Include CSRF token if your Django setup requires it for API calls
                    // 'X-CSRFToken': getCookie('csrftoken'), // Implement getCookie function if needed
                },
                // credentials: 'include' // Include if using sessions/cookies for auth
            });

            const result = await response.json();

            if (response.ok) {
                console.log(`âœ… handleDelete: Successfully deleted notification ${srNoToDelete}`);
                alert(result.message || 'Notification deleted successfully.');

                // Update the local state to remove the deleted notification
                setNotifications(prevNotifications =>
                    prevNotifications.filter(notification => notification.sr_no !== srNoToDelete)
                );
                setFilteredNotifications(prevFiltered =>
                    prevFiltered.filter(notification => notification.sr_no !== srNoToDelete)
                );

            } else {
                console.error(`âŒ handleDelete: Failed to delete notification ${srNoToDelete}`, result.error);
                alert(`Error deleting notification: ${result.error || 'Unknown error'}`);
            }
        } catch (err) {
            console.error(`ðŸ’¥ handleDelete: Network error deleting notification ${srNoToDelete}`, err);
            alert('Network error occurred while deleting notification.');
        }
    };
    // --- END NEW: Handler for Delete Button (with Role-Based Check) ---


    // --- NEW: Handler for Download CSV Button ---
    const handleDownloadCSV = () => {
        console.log("handleDownloadCSV: Initiating download...");

        // Construct query parameters based on current filters, sort, and search
        const params = new URLSearchParams({
            // Add filters if they are active
            ...(selectedType !== 'all' && { type: selectedType }),
            ...(selectedPriority !== 'all' && { priority: selectedPriority }),
            // ...(selectedDepartment !== 'all' && { department: selectedDepartmentUuid }), // If you have a department filter and its UUID
            // Add sorting
            sort_by: sortCriteria,
            sort_order: sortDirection,
            // Add search
            ...(searchQuery.trim() !== '' && { search: searchQuery.trim() }),
            // Add creator if needed (optional, maybe only for admin view)
            // created_by: currentUser?.employee_id, // Example
        });

        console.log("handleDownloadCSV: Query parameters for CSV download:", params.toString());

        // Construct the full URL for the CSV endpoint
        const csvDownloadUrl = `http://localhost:8001/api/circular/api/approved-notifications/download-csv/?${params}`;

        // Trigger the download by setting window.location.href
        // This is the standard way to trigger a file download from a link via JavaScript
        window.location.href = csvDownloadUrl;

        console.log("handleDownloadCSV: Download request sent to:", csvDownloadUrl);
    };
    // --- END NEW ---


    const handleSupersede = (notificationToSupersede) => {
        const srNoToSupersede = notificationToSupersede?.sr_no;
        if (!srNoToSupersede) {
            console.error("handleSupersede: Missing SR No for notification", notificationToSupersede);
            alert("Unable to supersede this notification because its serial number is missing.");
            return;
        }

        const currentUser = user;
        const redirectPath = currentUser
            ? (currentUser.role_name?.toLowerCase() === 'admin'
                ? '/circular/admin'
                : '/circular/office')
            : '/login';
        console.log(`ðŸš€ handleSupersede: Preparing to supersede notification ${srNoToSupersede}`);

        try {
            localStorage.setItem('supersedingNotificationId', srNoToSupersede); // Store the OLD SR No
            console.log(`âœ… handleSupersede: Stored supersedingNotificationId (${srNoToSupersede}) in localStorage`);

            localStorage.setItem('oldNotificationType', notificationToSupersede.msc_type || '');
            localStorage.setItem(
                'oldNotificationDept',
                notificationToSupersede.dept_name || notificationToSupersede.dept || '',
            );
            localStorage.setItem('oldNotificationCategory', notificationToSupersede.category || '');
            localStorage.setItem('oldNotificationPriority', notificationToSupersede.priority || '');

            const oldSubCatNames = parseCircularStoredArray(notificationToSupersede.sub_category);
            const oldSecondSubCatNames = parseCircularStoredArray(notificationToSupersede.second_sub_category);
            localStorage.setItem('oldNotificationSubCatNames', JSON.stringify(oldSubCatNames));
            localStorage.setItem('oldNotificationSecondSubCatNames', JSON.stringify(oldSecondSubCatNames));

            console.log(`âœ… handleSupersede: Stored old notification details in localStorage for pre-filling.`);

            // 4. Determine user type to redirect correctly
            if (currentUser) {
                if (currentUser.role_name?.toLowerCase() === 'admin') {
                    console.log("handleSupersede: Identified user as Admin, will redirect to /circular/admin");
                } else {
                    console.log("handleSupersede: Identified user as Office User, will redirect to /circular/office");
                }
            } else {
                console.warn("handleSupersede: No user found in localStorage, redirecting to login.");
            }

            // 5. Redirect the user to the appropriate form
            console.log(`handleSupersede: Redirecting user to ${redirectPath} to create superseding notification with pre-filled data`);
            window.location.href = redirectPath; // Use href for full page load to ensure state reset

            // Note: The actual database update for is_superseeded and superseeded_by
            // # will happen in the `create_notification` view when the new notification is submitted.
            // # This frontend handler just initiates the process by storing the OLD details and ID, then redirecting.

        } catch (storageError) {
            console.error(`âŒ handleSupersede: Error preparing supersede data for ${srNoToSupersede}:`, storageError);
            localStorage.setItem('supersedingNotificationId', srNoToSupersede);
            window.location.href = redirectPath;
        }

    };




    const getPriorityBadge = (priorityInput) => {
        // The priorityInput should now be the name string thanks to the mapping in Step 3
        const priority = priorityInput; // It's already the name

        // Normalize priority for safer comparison and mapping
        const normalizedPriority = (priority || '').toString(); // Ensure it's a string
        const map = {
            Low: "bg-green-100 text-green-700",
            Medium: "bg-yellow-100 text-yellow-700",
            High: "bg-orange-100 text-orange-700",
            Critical: "bg-red-100 text-red-700",
        };
        const style = map[normalizedPriority] || "bg-gray-100 text-gray-700";
        return (
            <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${style}`}
            >
                {normalizedPriority}
            </span>
        );
    };


    if (loading)
        return (
            <div className="flex justify-center items-center h-screen">
                <div className="flex flex-col items-center">
                    <Bell className="animate-bounce text-sky-600 w-8 h-8 mb-2" />
                    <p className="text-gray-500">Loading approved notifications...</p>
                </div>
            </div>
        );

    if (error)
        return (
            <div className="p-6 text-center text-red-600">
                <h2 className="text-xl font-semibold">Error</h2>
                <p>{error}</p>
            </div>
        );

    return (
         
        <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50 py-10">
            {/* Header */}
            <div className="text-center mb-6">
                <h1 className="text-2xl font-bold text-sky-800 tracking-tight">KSM Library</h1>
                <p className="text-gray-600 mt-1 text-sm">
                    View, search and download approved circulars, alerts & work instructions.
                </p>
            </div>

            {/* Compact Filter Toolbar */}
            <div className="max-w-7xl mx-auto mb-6 bg-white/95 shadow-md rounded-xl border border-sky-100 px-4 py-4">
                <div className="flex flex-wrap items-center justify-between gap-4">

                    {/* Left Section â€“ Search + Filters */}
                    <div className="flex flex-wrap items-center gap-4">

                        {/* Search */}
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-sky-400" />
                            <input
                                type="text"
                                placeholder="Search title, SR No, hashtags..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 pr-3 py-2 w-64 border border-sky-200 rounded-lg text-sm focus:ring-sky-400 focus:border-sky-400 bg-sky-50/50"
                            />
                        </div>

                        {/* Type */}
                        <select
                            value={selectedType}
                            onChange={(e) => setSelectedType(e.target.value)}
                            className="py-2 px-2 border border-sky-200 rounded-lg text-sm bg-white focus:ring-sky-400 focus:border-sky-400"
                        >
                            <option value="all">All Types</option>
                            <option value="alert">Alert</option>
                            <option value="circular">Circular</option>
                            <option value="workinstruction">Work Instruction</option>
                        </select>

                        {/* Priority */}
                        <select
                            value={selectedPriority}
                            onChange={(e) => setSelectedPriority(e.target.value)}
                            className="py-2 px-2 border border-sky-200 rounded-lg text-sm bg-white focus:ring-sky-400 focus:border-sky-400"
                        >
                            <option value="all">All Priorities</option>
                            <option value="Low">Low</option>
                            <option value="Medium">Medium</option>
                            <option value="High">High</option>
                            <option value="Critical">Critical</option>
                        </select>
                    </div>

                    {/* Right Section â€“ Sort & Buttons */}
                    <div className="flex items-center gap-3">

                        {/* Sort */}
                        <select
                            value={sortCriteria}
                            onChange={(e) => setSortCriteria(e.target.value)}
                            className="py-2 px-2 border border-gray-300 rounded-lg text-sm focus:ring-sky-400"
                        >
                            <option value="created_at">Date Created</option>
                            <option value="sr_no">SR No</option>
                        </select>

                        <select
                            value={sortDirection}
                            onChange={(e) => setSortDirection(e.target.value)}
                            className="py-2 px-2 border border-gray-300 rounded-lg text-sm focus:ring-sky-400"
                        >
                            <option value="desc">Descending</option>
                            <option value="asc">Ascending</option>
                        </select>

                        {/* CSV Button */}
                        <button
                            onClick={handleDownloadCSV}
                            className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700"
                            
                        >
                            <DownloadIcon size={14} />
                            CSV
                        </button>

                        {/* Reset */}
                        <button
                            onClick={resetFilters}
                            className="flex items-center gap-1 px-3 py-2 bg-sky-600 text-white rounded-lg text-sm hover:bg-sky-700"
                        >
                            <RefreshCcw size={14} />
                            Reset
                        </button>
                    </div>
                </div>
            </div>


            {/* Results */}
            <div className="max-w-7xl mx-auto">
                <p className="text-sm text-gray-600 mb-4">
                    Showing{" "}
                    <span className="font-semibold text-sky-700">
                        {filteredNotifications.length}
                    </span>{" "}
                    of {notifications.length} approved notifications
                </p>

                {filteredNotifications.length === 0 ? (
                    <div className="text-center py-20 text-gray-500">
                        No notifications match your filters.
                    </div>
                ) : (
                    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
                        {filteredNotifications.map((n) => (
                            // --- DEBUG: Log the notification object to see its properties ---
                            console.log("ApprovedNotificationsLibrary: Rendering notification card for SR No:", n.sr_no, "Object:", n),
                            // --- END DEBUG ---
                            // --- NEW: Highlight superseded notifications ---
                            <div
                                key={n.id}
                                // --- CHANGED: Log the is_superseeded value for this specific card ---
                                className={`bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-lg transition-all p-5 flex flex-col justify-between ${n.is_superseeded
                                    ? (console.log("  - Card for", n.sr_no, "is highlighted as superseded."), 'bg-yellow-50 border-yellow-200')
                                    : (console.log("  - Card for", n.sr_no, "is NOT highlighted as superseded."), '')
                                    }`}
                            // --- END CHANGED ---
                            >
                                {/* --- END NEW --- */}
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="text-xs text-gray-500">
                                            {new Date(n.created_at).toLocaleDateString()}
                                        </div>
                                        <div>{getPriorityBadge(n.priority)}</div>
                                    </div>
                                    <h3 className="text-lg font-semibold text-gray-800 mb-2 line-clamp-2">
                                        {n.title || n.sr_no}
                                    </h3>
                                    <div className="flex flex-wrap gap-2 mb-2">
                                        {getTypeBadge(n.msc_type)}
                                        {/* --- NEW: Display Hashtags --- */}
                                        {/* Check if hashtags exist and are not empty */}
                                        {n.hashtags && n.hashtags.trim() !== '' && (
                                            <div className="flex flex-wrap gap-1 mt-2">
                                                {n.hashtags
                                                    .split(/[\s,]+/) // split by space or comma
                                                    .filter(tag => tag.trim() !== '')
                                                    .map((tag, index) => (
                                                        <span
                                                            key={index}
                                                            className="px-2 py-0.5 text-xs font-medium rounded-full bg-gradient-to-r from-sky-100 via-sky-200 to-sky-100 text-sky-800 border border-sky-200 shadow-sm hover:shadow-md hover:scale-105 transition-transform duration-200 cursor-default"
                                                        >
                                                            #{tag.replace(/^#/, '')}
                                                        </span>
                                                    ))}
                                            </div>
                                        )}

                                        {/* --- END NEW: Display Hashtags --- */}
                                    </div>
                                </div>

                                {/* Buttons */}
                                <div className="mt-4 flex justify-between items-center">
                                    <div className="flex gap-2">
                                         <WithPermission id="PSC_P_020">
                                        {n.attachment_url ? (
                                            <a
                                                href={buildCircularAttachmentUrl(n.attachment_url)}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                process-id="PSC_P_020"
                                                className="flex items-center gap-1 px-3 py-1 text-sm font-medium text-indigo-700 bg-indigo-100 rounded-lg hover:bg-indigo-200 transition"
                                            >
                                                <FileDown size={14} />
                                            </a>
                                        ) : (
                                            <span className="text-gray-400 text-sm italic">
                                                No file
                                            </span>
                                        )}
                                        </WithPermission>

                                        {/* --- NEW: Supersede Button --- */}
                                         <WithPermission id="PSC_P_021">
                                        <button
                                            onClick={() => handleSupersede(n)}
                                            process-id="PSC_P_021"
                                            className="flex items-center justify-center w-9 h-9 rounded-full bg-amber-100 hover:bg-amber-200 text-amber-700 shadow-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-400"
                                            aria-label={`Supersede ${n.sr_no}`}
                                            title={`Supersede ${n.sr_no}`}
                                        >
                                            {/* Supersede SVG Icon */}
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
                                                    d="M4 4v5h.582m0 0A7.5 7.5 0 1112 19.5 7.5 7.5 0 014.582 9H9"
                                                />
                                            </svg>
                                        </button>
                                        </WithPermission>

                                        {/* --- END NEW: Supersede Button --- */}
                                            <WithPermission id="PSC_P_022">
                                        <button
                                            onClick={() => handleViewSeenCrews(n.sr_no)} // Pass the notification's SR No
                                            process-id="PSC_P_022"
                                            className="flex items-center justify-center w-9 h-9 rounded-full bg-green-100 hover:bg-green-200 text-green-700 shadow-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-400"
                                            aria-label={`View seen crews for ${n.sr_no}`}
                                            title={`View seen crews for ${n.sr_no}`}
                                        >
                                            <Eye size={14} /> {/* Use Eye icon for viewing seen crews */}
                                        </button>
                                        </WithPermission>

                                        {/* --- NEW: Delete Button --- */}
                                            <WithPermission id="PSC_P_023">
                                        <button
                                            onClick={() => handleDelete(n.sr_no)}
                                            process-id="PSC_P_023"
                                            className="flex items-center gap-1 px-3 py-1 text-sm font-medium text-red-700 bg-red-100 rounded-lg hover:bg-red-200 transition"
                                            aria-label={`Delete ${n.sr_no}`}
                                            title={`Delete ${n.sr_no}`}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                        </WithPermission>
                                        {/* --- END NEW: Delete Button --- */}


                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* --- NEW: View Seen Crews Modal --- */}

                {viewingSeenCrews && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                        <div className="bg-white rounded-xl shadow-xl w-full max-w-md max-h-[80vh] overflow-y-auto">
                            <div className="p-6">
                                <div className="flex justify-between items-center mb-4">
                                    <h2 className="text-lg font-semibold text-gray-800">Seen Crews for {viewingSeenCrews}</h2>
                                    <button
                                        onClick={() => setViewingSeenCrews(null)}
                                        className="text-gray-500 hover:text-gray-700"
                                    >
                                        &times;
                                    </button>
                                </div>

                                {loadingSeenCrews ? (
                                    <div className="text-center py-4">
                                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-sky-500 mx-auto"></div>
                                        <p className="text-gray-500 mt-2">Loading seen crews...</p>
                                    </div>
                                ) : (
                                    <>
                                        {seenCrewsData.length > 0 ? (
                                            <div className="space-y-2">
                                                {seenCrewsData.map((record, index) => (
                                                    <div key={index} className={`p-3 rounded-lg ${record.seen_at ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'} flex items-center justify-between`}>
                                                        <div className="flex-1">
                                                            <span className="font-medium">{record.crew_id}</span>
                                                            {record.seen_at ? (
                                                                <span className="text-sm text-green-700 ml-2">Seen at: {new Date(record.seen_at).toLocaleString()}</span>
                                                            ) : (
                                                                <span className="text-sm text-gray-500 ml-2">Not Seen</span>
                                                            )}
                                                        </div>
                                                        {/* --- NEW: Send Reminder Button (Bell Icon) for Individual Crew --- */}
                                                        {!record.seen_at && ( // Only show the button if the crew has NOT seen the notification
                                                            <button
                                                                onClick={() => handleSendIndividualReminder(viewingSeenCrews, record.crew_id)} // Pass the SR No and crew ID
                                                                className="ml-2 p-1 bg-amber-100 hover:bg-amber-200 text-amber-700 rounded-full transition"
                                                                title={`Send reminder to ${record.crew_id}`}
                                                            >
                                                                <Bell size={16} />
                                                            </button>
                                                        )}
                                                        {/* --- END NEW: Send Reminder Button --- */}

                                                        {/* Optionally display reminder_sent_at */}
                                                        {record.reminder_sent_at && (
                                                            <div className="text-xs text-amber-600 ml-2">
                                                                Reminder sent at: {new Date(record.reminder_sent_at).toLocaleString()}
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="text-center py-4">
                                                <p className="text-gray-500">No crew members have seen this notification yet.</p>
                                            </div>
                                        )}
                                    </>
                                )}

                                <div className="mt-4 text-xs text-gray-500">
                                    {/* * Green background indicates the crew has seen the notification.
                    <br /> */}
                                    * Click on Bell icon to send reminder.
                                </div>
                            </div>
                        </div>
                    </div>
                )}
                {/* --- END NEW: View Seen Crews Modal --- */}
            </div>
        </div>
      
    );
};

export default ApprovedNotificationsLibrary;
