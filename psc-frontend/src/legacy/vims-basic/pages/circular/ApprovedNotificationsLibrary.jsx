// src/components/ApprovedNotificationsLibrary.jsx
import React, { useState, useEffect } from "react";
import {
    RefreshCcw,
    FileDown,
    Bell,
    BellRing,
    Search,
    Trash2,
    Eye,
    FileText
} from "lucide-react";
import { Download as DownloadIcon } from 'lucide-react';
import { WithPermission } from '../../utils/circular/permissionUtils';
import { useAuth } from '../../hooks/auth/useAuth';
import { PageHeader } from '@/components/layout/page-header';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '../../components/circular/ui/card';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '../../components/circular/ui/table';



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
    const [crewSearchQuery, setCrewSearchQuery] = useState("");
    const [sendingIndividualReminder, setSendingIndividualReminder] = useState(null); // Store the crew_id being processed for individual reminder
    const [typeUuidToNameMap, setTypeUuidToNameMap] = useState({});
    const [priorityUuidToNameMap, setPriorityUuidToNameMap] = useState({});
    const [loadingLookupMaps, setLoadingLookupMaps] = useState(true); // To track loading of lookup data





    const filteredSeenCrewsData = seenCrewsData.filter((record) => {
        const query = crewSearchQuery.trim().toLowerCase();
        if (!query) return true;
        return String(record.crew_id || '').toLowerCase().includes(query);
    });


    // --- NEW: Fetch Lookup Maps on Component Mount ---
    useEffect(() => {
        const fetchLookupMaps = async () => {
            // console.log("ApprovedNotificationsLibrary: Fetching lookup maps (type, priority)...");
            try {
                // Fetch Document Types
                const typeRes = await fetch('http://localhost:8000/api/circular/api/document-types/');
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
                const priorityRes = await fetch('http://localhost:8000/api/circular/api/priorities/');
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
                    "http://localhost:8000/api/circular/api/approved-notifications/"
                );
                if (!response.ok) {
                    throw new Error(`Failed to fetch notifications: ${response.status} ${response.statusText}`);
                }
                const data = await response.json();
                // console.log("ApprovedNotificationsLibrary: Fetched raw notifications ", data);

                const notificationsWithNames = data.map(notification => ({
                    ...notification,
                    title: notification.office_instructions || notification.title || '',
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
            result = result.filter(
                (n) => n.msc_type && n.msc_type.toLowerCase() === selectedType
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
        const normalizedType = (type || '').toLowerCase();
        const map = {
            alert: "bg-red-100 text-red-700",
            circular: "bg-blue-100 text-blue-700",
            workinstruction: "bg-amber-100 text-amber-700",
            work_instruction: "bg-amber-100 text-amber-700", // Handle potential underscore
        };
        const style = map[normalizedType] || "bg-gray-100 text-gray-700";
        const displayText = normalizedType
            .replace(/_/g, ' ') // Replace underscores with spaces
            .split(' ')
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
        console.log("🔔 handleSendReminder: Sending reminder for notification SR No:", srNoForReminder);
        const confirmed = window.confirm(`Are you sure you want to send a reminder for notification ${srNoForReminder}?`);
        if (!confirmed) {
            console.log("handleSendReminder: User cancelled reminder.");
            return; // Stop if user cancels
        }

        try {
            // Call the backend endpoint to update the reminder_sent_at field
            const response = await fetch(`http://localhost:8000/api/circular/api/notifications/${srNoForReminder}/send-reminder/`, { // Use your new reminder endpoint
                method: 'POST', // Use POST for state-changing actions
                headers: {
                    'Content-Type': 'application/json',
                    // 'X-CSRFToken': getCookie('csrftoken'), // Add if needed
                },
                // credentials: 'include' // Include if using sessions/cookies for auth
            });

            const result = await response.json();

            if (response.ok) {
                console.log("✅ handleSendReminder: Reminder sent successfully for notification", srNoForReminder);
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
        console.log("🚀 handleViewSeenCrews: Fetching seen crews for notification SR No:", notificationSrNo);
        setViewingSeenCrews(notificationSrNo); // Set the SR No to view
        setLoadingSeenCrews(true); // Start loading

        try {
            const response = await fetch(`http://localhost:8000/api/circular/api/notifications/${notificationSrNo}/crew-delivery-status/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            const result = await response.json();

            if (response.ok) {
                console.log("✅ handleViewSeenCrews: Successfully fetched delivery records for notification", notificationSrNo);
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
        console.log(`🔔 handleSendIndividualReminder: Sending individual reminder for notification ${notificationSrNo} to crew ${crewId}`);
        const confirmed = window.confirm(`Are you sure you want to send a reminder to crew ${crewId} for notification ${notificationSrNo}?`);
        if (!confirmed) {
            console.log("handleSendIndividualReminder: User cancelled individual reminder.");
            return; // Stop if user cancels
        }

        // Set loading state for this specific crew
        setSendingIndividualReminder(crewId);

        try {
            // Call the backend endpoint to update the reminder_sent_at field for this specific crew and notification
            const response = await fetch(`http://localhost:8000/api/circular/api/notifications/${notificationSrNo}/send-individual-reminder/`, { // Use your new endpoint
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
                console.log("✅ handleSendIndividualReminder: Individual reminder sent successfully for crew", crewId);
                alert(`Reminder sent successfully to crew ${crewId}.`);
                setSeenCrewsData((prev) =>
                    prev.map((record) =>
                        record.crew_id === crewId
                            ? { ...record, reminder_sent_at: new Date().toISOString() }
                            : record
                    )
                );

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
        console.log(`🚀 handleDelete: Attempting to delete notification ${srNoToDelete}`);

        // --- REMOVED: Admin Role Check ---
        // Any user can now attempt to delete
        // --- END REMOVED: Admin Role Check ---

        const confirmed = window.confirm(`Are you sure you want to delete notification ${srNoToDelete}? This action cannot be undone.`);
        if (!confirmed) {
            console.log("handleDelete: User cancelled deletion.");
            return;
        }

        try {
            const response = await fetch(`http://localhost:8000/api/circular/api/notifications/${srNoToDelete}/delete/`, {
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
                console.log(`✅ handleDelete: Successfully deleted notification ${srNoToDelete}`);
                alert(result.message || 'Notification deleted successfully.');

                // Update the local state to remove the deleted notification
                setNotifications(prevNotifications =>
                    prevNotifications.filter(notification => notification.sr_no !== srNoToDelete)
                );
                setFilteredNotifications(prevFiltered =>
                    prevFiltered.filter(notification => notification.sr_no !== srNoToDelete)
                );

            } else {
                console.error(`❌ handleDelete: Failed to delete notification ${srNoToDelete}`, result.error);
                alert(`Error deleting notification: ${result.error || 'Unknown error'}`);
            }
        } catch (err) {
            console.error(`💥 handleDelete: Network error deleting notification ${srNoToDelete}`, err);
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
        const csvDownloadUrl = `http://localhost:8000/api/circular/api/approved-notifications/download-csv/?${params}`;

        // Trigger the download by setting window.location.href
        // This is the standard way to trigger a file download from a link via JavaScript
        window.location.href = csvDownloadUrl;

        console.log("handleDownloadCSV: Download request sent to:", csvDownloadUrl);
    };
    // --- END NEW ---


    const handleSupersede = async (srNoToSupersede) => {
        console.log(`🚀 handleSupersede: Preparing to supersede notification ${srNoToSupersede}`);

        try {
            // 1. Fetch the DETAILS of the notification being superseded
            console.log(`handleSupersede: Fetching details for notification ${srNoToSupersede} to pre-fill form.`);
            const detailsResponse = await fetch(`http://localhost:8000/api/circular/api/submitted/${srNoToSupersede}/`);
            if (!detailsResponse.ok) {
                throw new Error(`Failed to fetch notification details for supersede: ${detailsResponse.status} ${detailsResponse.statusText}`);
            }
            const oldNotificationDetails = await detailsResponse.json();
            console.log(`handleSupersede: Retrieved details for old notification ${srNoToSupersede}:`, oldNotificationDetails);

            // 2. Store the OLD SR No (for linking the new to the old in the backend)
            localStorage.setItem('supersedingNotificationId', srNoToSupersede); // Store the OLD SR No
            console.log(`✅ handleSupersede: Stored supersedingNotificationId (${srNoToSupersede}) in localStorage`);

            // 3. Store the OLD notification's details (for pre-filling the form)
            // Use the exact key names that the pre-fill useEffect expects
            localStorage.setItem('oldNotificationType', oldNotificationDetails.msc_type || ''); // Key name: 'oldNotificationType'
            localStorage.setItem('oldNotificationDept', oldNotificationDetails.dept === 0 ? 'seq' : oldNotificationDetails.dept === 1 ? 'technical' : ''); //  Key name: 'oldNotificationDept'
            localStorage.setItem('oldNotificationCategory', oldNotificationDetails.category || ''); //  Key name: 'oldNotificationCategory'
            localStorage.setItem('oldNotificationPriority', oldNotificationDetails.priority || ''); //  Key name: 'oldNotificationPriority'

            // Store sub-categories as JSON strings
            const oldSubCatNames = oldNotificationDetails.sub_category ? oldNotificationDetails.sub_category.split(',').map(s => s.trim()).filter(s => s) : [];
            const oldSecondSubCatNames = oldNotificationDetails.second_sub_category ? oldNotificationDetails.second_sub_category.split(',').map(s => s.trim()).filter(s => s) : [];
            localStorage.setItem('oldNotificationSubCatNames', JSON.stringify(oldSubCatNames)); //  Key name: 'oldNotificationSubCatNames'
            localStorage.setItem('oldNotificationSecondSubCatNames', JSON.stringify(oldSecondSubCatNames)); //  Key name: 'oldNotificationSecondSubCatNames'

            console.log(`✅ handleSupersede: Stored old notification details in localStorage for pre-filling.`);

            // 4. Determine user type to redirect correctly
            const currentUser = user
            let redirectPath = '/';
            if (currentUser) {
                if (currentUser.employee_id === 'Prince.S') {
                    redirectPath = '/admin'; // Redirect to Admin panel
                    console.log("handleSupersede: Identified user as Admin, will redirect to /admin");
                } else {
                    redirectPath = '/office'; // Redirect to Office User panel
                    console.log("handleSupersede: Identified user as Office User, will redirect to /office");
                }
            } else {
                console.warn("handleSupersede: No user found in localStorage, redirecting to login.");
                redirectPath = '/login';
            }

            // 5. Redirect the user to the appropriate form
            console.log(`handleSupersede: Redirecting user to ${redirectPath} to create superseding notification with pre-filled data`);
            window.location.href = redirectPath; // Use href for full page load to ensure state reset

            // Note: The actual database update for is_superseeded and superseeded_by
            // # will happen in the `create_notification` view when the new notification is submitted.
            // # This frontend handler just initiates the process by storing the OLD details and ID, then redirecting.

        } catch (fetchError) {
            console.error(`❌ handleSupersede: Error fetching old notification details for ${srNoToSupersede}:`, fetchError);
            alert(`Failed to fetch details for notification ${srNoToSupersede}. Cannot pre-fill form. Proceeding without pre-fill.`);
            // Optionally, still proceed with just the SR No if fetching details fails
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
         
        <div className="space-y-6">
            <PageHeader
                title="KSM Library"
                subtitle="View, search and download approved circulars, alerts and work instructions."
            />

            <div className="rounded-lg border border-neutral-200 bg-white p-4 shadow-md">
                <div className="flex flex-wrap items-center justify-between gap-4">

                    {/* Left Section – Search + Filters */}
                    <div className="flex flex-wrap items-center gap-4">

                        {/* Search */}
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
                            <input
                                type="text"
                                placeholder="Search title, SR No, hashtags..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="h-10 w-64 rounded-md border border-neutral-300 bg-white pl-9 pr-3 text-sm text-neutral-800 placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                            />
                        </div>

                        {/* Type */}
                        <select
                            value={selectedType}
                            onChange={(e) => setSelectedType(e.target.value)}
                            className="h-10 rounded-md border border-neutral-300 bg-white px-3 text-sm text-neutral-800 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
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
                            className="h-10 rounded-md border border-neutral-300 bg-white px-3 text-sm text-neutral-800 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                        >
                            <option value="all">All Priorities</option>
                            <option value="Low">Low</option>
                            <option value="Medium">Medium</option>
                            <option value="High">High</option>
                            <option value="Critical">Critical</option>
                        </select>
                    </div>

                    {/* Right Section – Sort & Buttons */}
                    <div className="flex items-center gap-3">

                        {/* Sort */}
                        <select
                            value={sortCriteria}
                            onChange={(e) => setSortCriteria(e.target.value)}
                            className="h-10 rounded-md border border-neutral-300 bg-white px-3 text-sm text-neutral-800 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                        >
                            <option value="created_at">Date Created</option>
                            <option value="sr_no">SR No</option>
                        </select>

                        <select
                            value={sortDirection}
                            onChange={(e) => setSortDirection(e.target.value)}
                            className="h-10 rounded-md border border-neutral-300 bg-white px-3 text-sm text-neutral-800 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                        >
                            <option value="desc">Descending</option>
                            <option value="asc">Ascending</option>
                        </select>

                        {/* CSV Button */}
                        <Button
                            onClick={handleDownloadCSV}
                            className="bg-success-600 text-white hover:bg-success-700"
                        >
                            <DownloadIcon size={14} />
                            CSV
                        </Button>

                        {/* Reset */}
                        <Button
                            onClick={resetFilters}
                            className="gap-1"
                        >
                            <RefreshCcw size={14} />
                            Reset
                        </Button>
                    </div>
                </div>
            </div>


            {/* Results */}
            <div>
                <p className="mb-4 text-sm text-neutral-600">
                    Showing{" "}
                    <span className="font-semibold text-neutral-800">
                        {filteredNotifications.length}
                    </span>{" "}
                    of {notifications.length} approved notifications
                </p>

                {filteredNotifications.length === 0 ? (
                    <div className="rounded-lg border border-dashed border-neutral-200 bg-white py-20 text-center text-neutral-500">
                        No notifications match your filters.
                    </div>
                ) : (
                    <div className="space-y-3">
                        {filteredNotifications.map((n) => (
                            <Card
                                key={n.id}
                                className={`border-l-4 border-l-error-500 transition-shadow hover:shadow-md ${n.is_superseeded ? 'border-warning-100 bg-warning-50/40' : ''}`}
                            >
                                <CardContent className="p-4">
                                    <div className="mb-3 flex items-start justify-between gap-3">
                                        <div className="min-w-0">
                                            <div className="font-medium text-neutral-900">{n.sr_no || '—'}</div>
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                            <WithPermission id="PSC_P_020">
                                                {n.attachment_url ? (
                                                    <a
                                                        href={`http://localhost:8000${n.attachment_url}`}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        process-id="PSC_P_020"
                                                        className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-neutral-200 bg-white text-neutral-700 shadow-sm transition-colors hover:border-neutral-300 hover:bg-neutral-50"
                                                        title={`Download ${n.sr_no}`}
                                                    >
                                                        <FileDown size={14} />
                                                    </a>
                                                ) : null}
                                            </WithPermission>

                                            <WithPermission id="PSC_P_021">
                                                <button
                                                    onClick={() => handleSupersede(n.sr_no)}
                                                    process-id="PSC_P_021"
                                                    className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-warning-100 bg-warning-50 text-warning-700 shadow-sm transition-colors hover:bg-warning-100"
                                                    aria-label={`Supersede ${n.sr_no}`}
                                                    title={`Supersede ${n.sr_no}`}
                                                >
                                                    <svg
                                                        xmlns="http://www.w3.org/2000/svg"
                                                        fill="none"
                                                        viewBox="0 0 24 24"
                                                        strokeWidth={2}
                                                        stroke="currentColor"
                                                        className="h-4 w-4"
                                                    >
                                                        <path
                                                            strokeLinecap="round"
                                                            strokeLinejoin="round"
                                                            d="M4 4v5h.582m0 0A7.5 7.5 0 1112 19.5 7.5 7.5 0 014.582 9H9"
                                                        />
                                                    </svg>
                                                </button>
                                            </WithPermission>

                                            <WithPermission id="PSC_P_022">
                                                <button
                                                    onClick={() => handleViewSeenCrews(n.sr_no)}
                                                    process-id="PSC_P_022"
                                                    className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-success-100 bg-success-50 text-success-700 shadow-sm transition-colors hover:bg-success-100"
                                                    aria-label={`View seen crews for ${n.sr_no}`}
                                                    title={`View seen crews for ${n.sr_no}`}
                                                >
                                                    <Eye size={14} />
                                                </button>
                                            </WithPermission>

                                            <WithPermission id="PSC_P_023">
                                                <button
                                                    onClick={() => handleDelete(n.sr_no)}
                                                    process-id="PSC_P_023"
                                                    className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-error-100 bg-error-50 text-error-700 shadow-sm transition-colors hover:bg-error-100"
                                                    aria-label={`Delete ${n.sr_no}`}
                                                    title={`Delete ${n.sr_no}`}
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            </WithPermission>
                                        </div>
                                    </div>

                                    <div className="mb-3 flex items-start gap-3">
                                        <div className="mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-primary-100 bg-primary-50 text-primary-700 shadow-sm">
                                            <FileText className="h-4 w-4" />
                                        </div>
                                        <div className="min-w-0 flex-1">
                                            <div className="truncate text-[17px] font-semibold leading-7 text-neutral-900" title={n.title || n.sr_no}>
                                                {n.title || n.sr_no}
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}

                {/* --- NEW: View Seen Crews Modal --- */}

                {viewingSeenCrews && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                        <div className="w-full max-w-md max-h-[80vh] overflow-hidden rounded-xl bg-white shadow-xl">
                            <div className="max-h-[80vh] overflow-y-auto">
                                <div className="sticky top-0 z-10 flex items-center justify-between border-b border-neutral-200 bg-white px-6 py-4">
                                    <h2 className="text-lg font-semibold text-gray-800">Seen Crews for {viewingSeenCrews}</h2>
                                    <button
                                        onClick={() => {
                                            setViewingSeenCrews(null);
                                            setCrewSearchQuery("");
                                        }}
                                        className="rounded-md p-1 text-gray-500 transition hover:bg-neutral-100 hover:text-gray-700"
                                        aria-label="Close seen crews modal"
                                    >
                                        &times;
                                    </button>
                                </div>
                                <div className="sticky top-[65px] z-10 border-b border-neutral-200 bg-white px-6 pb-4 pt-4">
                                    <div className="relative">
                                        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
                                        <input
                                            type="text"
                                            value={crewSearchQuery}
                                            onChange={(e) => setCrewSearchQuery(e.target.value)}
                                            placeholder="Search crew ID..."
                                            className="h-10 w-full rounded-lg border border-neutral-300 bg-white pl-10 pr-3 text-sm text-neutral-800 placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                                        />
                                    </div>
                                </div>
                                <div className="p-6">

                                {loadingSeenCrews ? (
                                    <div className="text-center py-4">
                                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-sky-500 mx-auto"></div>
                                        <p className="text-gray-500 mt-2">Loading seen crews...</p>
                                    </div>
                                ) : (
                                    <>
                                        {filteredSeenCrewsData.length > 0 ? (
                                            <div className="space-y-2">
                                                {filteredSeenCrewsData.map((record, index) => (
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
                                                            record.reminder_sent_at ? (
                                                                <div
                                                                    className="ml-2 inline-flex items-center gap-1 rounded-full bg-warning-50 px-2 py-1 text-xs font-medium text-warning-700"
                                                                    title={`Reminder already sent to ${record.crew_id}`}
                                                                >
                                                                    <BellRing size={14} />
                                                                    Reminded
                                                                </div>
                                                            ) : (
                                                                <button
                                                                    onClick={() => handleSendIndividualReminder(viewingSeenCrews, record.crew_id)} // Pass the SR No and crew ID
                                                                    disabled={sendingIndividualReminder === record.crew_id}
                                                                    className="ml-2 rounded-full bg-amber-100 p-1 text-amber-700 transition hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-60"
                                                                    title={
                                                                        sendingIndividualReminder === record.crew_id
                                                                            ? `Sending reminder to ${record.crew_id}`
                                                                            : `Send reminder to ${record.crew_id}`
                                                                    }
                                                                >
                                                                    <Bell size={16} className={sendingIndividualReminder === record.crew_id ? 'animate-pulse' : ''} />
                                                                </button>
                                                            )
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
                                                <p className="text-gray-500">
                                                    {seenCrewsData.length > 0 ? 'No crew members match your search.' : 'No crew members have seen this notification yet.'}
                                                </p>
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
                    </div>
                )}
                {/* --- END NEW: View Seen Crews Modal --- */}
            </div>
        </div>
      
    );
};

export default ApprovedNotificationsLibrary;
