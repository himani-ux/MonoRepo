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
import { buildCircularAttachmentUrl } from '../../utils/circular/attachmentUrl';
import { parseCircularStoredArray } from '../../utils/circular/supersede';
import {
    getCircularRankDisplayName,
    getDisplayableCircularRanks,
    splitCircularRanksByDepartment,
} from '../../utils/circular/ranks';



const APPROVED_NOTIFICATIONS_PER_PAGE = 15;

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
    const [currentPage, setCurrentPage] = useState(1);
    const [crewSearchQuery, setCrewSearchQuery] = useState("");
    const [sendingIndividualReminder, setSendingIndividualReminder] = useState(null); // Store the crew_id being processed for individual reminder
    const [typeUuidToNameMap, setTypeUuidToNameMap] = useState({});
    const [priorityUuidToNameMap, setPriorityUuidToNameMap] = useState({});
    const [loadingLookupMaps, setLoadingLookupMaps] = useState(true); // To track loading of lookup data
    const [expandedTitle, setExpandedTitle] = useState(null);
    const [showResendModal, setShowResendModal] = useState(false);
    const [resendNotification, setResendNotification] = useState(null);
    const [resendComment, setResendComment] = useState("");
    const [resendVessels, setResendVessels] = useState([]);
    const [resendSelectedVesselIds, setResendSelectedVesselIds] = useState(new Set());
    const [resendRanks, setResendRanks] = useState([]);
    const [resendSelectedRankIds, setResendSelectedRankIds] = useState(new Set());
    const [loadingResendOptions, setLoadingResendOptions] = useState(false);
    const [isResendSubmitting, setIsResendSubmitting] = useState(false);

    const normalizeNotificationTitle = (notification) => {
        const rawTitle = notification?.title;
        if (typeof rawTitle === "string") {
            const normalizedTitle = rawTitle.replace(/\r\n|\n/g, " ").trim();
            if (normalizedTitle) {
                return normalizedTitle;
            }
        }
        return "No title";
    };

    const normalizeHashtags = (value) => {
        if (Array.isArray(value)) {
            return value
                .map((tag) => String(tag || "").trim())
                .filter(Boolean);
        }

        if (typeof value === "string") {
            return value
                .split(/[\s,]+/)
                .map((tag) => tag.trim())
                .filter(Boolean);
        }

        return [];
    };

    const normalizeCircularTypeToken = (value) => {
        return String(value ?? "")
            .toLowerCase()
            .replace(/[^a-z0-9]/g, "");
    };

    const getCrewPrimaryLabel = (record) => {
        return record?.crew_name || record?.resolved_crew_id || record?.crew_id || "Unknown Crew";
    };

    const getCrewSecondaryLabel = (record) => {
        const secondaryParts = [];
        if (record?.rank_name) {
            secondaryParts.push(record.rank_name);
        }
        if (record?.vessel_name) {
            secondaryParts.push(record.vessel_name);
        }
        if (record?.resolved_crew_id) {
            secondaryParts.push(`Crew ID: ${record.resolved_crew_id}`);
        } else if (record?.crew_id) {
            secondaryParts.push(`Crew Ref: ${record.crew_id}`);
        }
        return secondaryParts.join(" | ");
    };

    const getCrewSearchText = (record) => {
        return [
            record?.rank_name,
            record?.vessel_name,
            record?.crew_status_name,
            record?.crew_name,
            record?.resolved_crew_id,
            record?.crew_id,
        ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();
    };

    const openTitleModal = (title) => {
        const normalizedTitle = String(title || '').trim();
        if (!normalizedTitle) return;
        setExpandedTitle(normalizedTitle);
    };

    const closeTitleModal = () => {
        setExpandedTitle(null);
    };





    const filteredSeenCrewsData = seenCrewsData.filter((record) => {
        const query = crewSearchQuery.trim().toLowerCase();
        if (!query) return true;
        return getCrewSearchText(record).includes(query);
    });

    const seenCrewStats = {
        total: seenCrewsData.length,
        seen: seenCrewsData.filter((record) => Boolean(record?.seen_at)).length,
        unread: seenCrewsData.filter((record) => !record?.seen_at).length,
        reminded: seenCrewsData.filter((record) => Boolean(record?.reminder_sent_at)).length,
    };

    const formatCrewDateTime = (value) => {
        if (!value) return null;
        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) {
            return value;
        }
        return parsed.toLocaleString();
    };

    const {
        deckRanks: resendDeckRanks,
        technicalRanks: resendTechnicalRanks,
    } = splitCircularRanksByDepartment(resendRanks);


    // --- NEW: Fetch Lookup Maps on Component Mount ---
    useEffect(() => {
        const fetchLookupMaps = async () => {
            // console.log("ApprovedNotificationsLibrary: Fetching lookup maps (type, priority)...");
            try {
                // Fetch Document Types
                const typeRes = await fetch('/api/circular/api/document-types/');
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
                const priorityRes = await fetch('/api/circular/api/priorities/');
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

    const loadApprovedNotifications = async () => {
        try {
            setLoading(true);
            const response = await fetch(
                "/api/circular/api/approved-notifications/"
            );
            if (!response.ok) {
                throw new Error(`Failed to fetch notifications: ${response.status} ${response.statusText}`);
            }
            const data = await response.json();

            const notificationsWithNames = data.map(notification => {
                const hashtags = normalizeHashtags(notification.hashtags);
                return {
                    ...notification,
                    title: normalizeNotificationTitle(notification),
                    hashtags,
                    hashtagsText: hashtags.join(' '),
                    msc_type: typeUuidToNameMap[notification.msc_type] || notification.msc_type,
                    priority: priorityUuidToNameMap[notification.priority] || notification.priority,
                };
            });

            setNotifications(notificationsWithNames);
            setFilteredNotifications(notificationsWithNames);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (loadingLookupMaps) {
            console.log("ApprovedNotificationsLibrary: Waiting for lookup maps to load before fetching notifications.");
            return;
        }

        if (error) {
            console.log("ApprovedNotificationsLibrary: Lookup maps failed to load, skipping notification fetch.");
            // return;
        }

        loadApprovedNotifications();
    }, [loadingLookupMaps, error]);




    useEffect(() => {
        let result = [...notifications];


        if (searchQuery.trim() !== "") {
            const query = searchQuery.trim().toLowerCase();
            result = result.filter((n) =>
                (n.title && n.title.toLowerCase().includes(query)) ||
                (n.sr_no && n.sr_no.toLowerCase().includes(query)) ||
                (n.hashtagsText && n.hashtagsText.toLowerCase().includes(query))
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

    useEffect(() => {
        setCurrentPage(1);
    }, [selectedType, selectedPriority, sortCriteria, sortDirection, searchQuery]);

    const totalPages = Math.max(
        1,
        Math.ceil(filteredNotifications.length / APPROVED_NOTIFICATIONS_PER_PAGE),
    );
    const safeCurrentPage = Math.min(currentPage, totalPages);
    const pageStartIndex = (safeCurrentPage - 1) * APPROVED_NOTIFICATIONS_PER_PAGE;
    const paginatedNotifications = filteredNotifications.slice(
        pageStartIndex,
        pageStartIndex + APPROVED_NOTIFICATIONS_PER_PAGE,
    );
    const paginationPages = Array.from({ length: totalPages }, (_, index) => index + 1);

    useEffect(() => {
        if (currentPage > totalPages) {
            setCurrentPage(totalPages);
        }
    }, [currentPage, totalPages]);


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
    const closeResendModal = (force = false) => {
        if (isResendSubmitting && !force) {
            return;
        }

        setShowResendModal(false);
        setResendNotification(null);
        setResendComment("");
        setResendVessels([]);
        setResendSelectedVesselIds(new Set());
        setResendRanks([]);
        setResendSelectedRankIds(new Set());
        setLoadingResendOptions(false);
    };

    const handleOpenResendModal = async (notification) => {
        setResendNotification(notification);
        setResendComment(notification?.publish_comment || "");
        setResendSelectedVesselIds(new Set());
        setResendSelectedRankIds(new Set());
        setResendVessels([]);
        setResendRanks([]);
        setShowResendModal(true);
        setLoadingResendOptions(true);

        try {
            const [vesselsResponse, ranksResponse] = await Promise.all([
                fetch("/api/circular/api/vessels/"),
                fetch("/api/circular/api/ranks/"),
            ]);

            if (!vesselsResponse.ok) {
                throw new Error(`Failed to fetch vessels: ${vesselsResponse.status} ${vesselsResponse.statusText}`);
            }

            if (!ranksResponse.ok) {
                throw new Error(`Failed to fetch ranks: ${ranksResponse.status} ${ranksResponse.statusText}`);
            }

            const [vesselsData, ranksData] = await Promise.all([
                vesselsResponse.json(),
                ranksResponse.json(),
            ]);

            setResendVessels(Array.isArray(vesselsData) ? vesselsData : []);
            setResendRanks(getDisplayableCircularRanks(ranksData));
        } catch (err) {
            console.error("handleOpenResendModal: Failed to load resend options:", err);
            alert(`Failed to load resend options: ${err.message}`);
            setShowResendModal(false);
            setResendNotification(null);
        } finally {
            setLoadingResendOptions(false);
        }
    };

    const handleResendVesselToggle = (vesselId) => {
        setResendSelectedVesselIds((prev) => {
            const next = new Set(prev);
            if (next.has(vesselId)) {
                next.delete(vesselId);
            } else {
                next.add(vesselId);
            }
            return next;
        });
    };

    const handleSelectAllResendVessels = () => {
        if (resendSelectedVesselIds.size === resendVessels.length && resendVessels.length > 0) {
            setResendSelectedVesselIds(new Set());
            return;
        }

        setResendSelectedVesselIds(new Set(resendVessels.map((vessel) => vessel.id)));
    };

    const handleResendRankToggle = (rankId) => {
        setResendSelectedRankIds((prev) => {
            const next = new Set(prev);
            if (next.has(rankId)) {
                next.delete(rankId);
            } else {
                next.add(rankId);
            }
            return next;
        });
    };

    const toggleResendRankGroup = (ranks) => {
        const rankIds = new Set(ranks.map((rank) => rank.id));
        const groupFullySelected = ranks.length > 0 && ranks.every((rank) => resendSelectedRankIds.has(rank.id));

        setResendSelectedRankIds((prev) => {
            const next = new Set(prev);
            if (groupFullySelected) {
                rankIds.forEach((id) => next.delete(id));
            } else {
                rankIds.forEach((id) => next.add(id));
            }
            return next;
        });
    };

    const handleSelectAllResendRanks = () => {
        if (resendSelectedRankIds.size === resendRanks.length && resendRanks.length > 0) {
            setResendSelectedRankIds(new Set());
            return;
        }

        setResendSelectedRankIds(new Set(resendRanks.map((rank) => rank.id)));
    };

    const handleConfirmResendApproval = async () => {
        if (isResendSubmitting) {
            return;
        }

        if (!resendNotification?.sr_no) {
            alert("Circular information is missing. Please try again.");
            return;
        }

        if (!user?.employee_id) {
            alert("You must be logged in to resend a circular.");
            return;
        }

        const selectedVesselIds = Array.from(resendSelectedVesselIds);
        const selectedRankIds = Array.from(resendSelectedRankIds);

        setIsResendSubmitting(true);

        try {
            const approvalResponse = await fetch(
                `/api/circular/api/notifications/${resendNotification.sr_no}/update-status/`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        publish_status: 2,
                        publish_comment: resendComment || "",
                        published_by: user.employee_id,
                        published_on: new Date().toISOString(),
                        vessel_ids: selectedVesselIds,
                        resend_approval: true,
                    }),
                }
            );
            const approvalResult = await approvalResponse.json();
            if (!approvalResponse.ok) {
                throw new Error(approvalResult.error || "Failed to rerun approval.");
            }

            if (selectedVesselIds.length > 0) {
                const vesselResponse = await fetch(
                    "/api/circular/api/notifications/send-emails/",
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            notification_sr_no: resendNotification.sr_no,
                            vessel_ids: selectedVesselIds,
                        }),
                    }
                );
                const vesselResult = await vesselResponse.json();
                if (!vesselResponse.ok) {
                    throw new Error(vesselResult.error || "Failed to send circular to selected vessels.");
                }
            }

            if (selectedRankIds.length > 0) {
                const rankResponse = await fetch(
                    `/api/circular/api/notifications/${resendNotification.sr_no}/link-ranks/`,
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            notification_sr_no: resendNotification.sr_no,
                            selected_rank_ids: selectedRankIds,
                        }),
                    }
                );
                const rankResult = await rankResponse.json();
                if (!rankResponse.ok) {
                    throw new Error(rankResult.error || "Failed to link selected ranks.");
                }
            }

            await loadApprovedNotifications();
            closeResendModal(true);
            alert("Circular approval process repeated successfully.");
        } catch (err) {
            console.error("handleConfirmResendApproval: Error while resending circular:", err);
            alert(err.message || "Failed to resend circular.");
        } finally {
            setIsResendSubmitting(false);
        }
    };



    // --- NEW: Handler for View Seen Crews Button ---
    const handleViewSeenCrews = async (notificationSrNo) => { // Accept the SR No string
        console.log("🚀 handleViewSeenCrews: Fetching seen crews for notification SR No:", notificationSrNo);
        setViewingSeenCrews(notificationSrNo); // Set the SR No to view
        setLoadingSeenCrews(true); // Start loading

        try {
            const response = await fetch(`/api/circular/api/notifications/${notificationSrNo}/crew-delivery-status/`, {
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
    const handleSendIndividualReminder = async (notificationSrNo, crewId, crewLabel = null) => {
        const targetCrewLabel = crewLabel || crewId;
        console.log(`🔔 handleSendIndividualReminder: Sending individual reminder for notification ${notificationSrNo} to crew ${crewId}`);
        const confirmed = window.confirm(`Are you sure you want to send a reminder to ${targetCrewLabel} for notification ${notificationSrNo}?`);
        if (!confirmed) {
            console.log("handleSendIndividualReminder: User cancelled individual reminder.");
            return; // Stop if user cancels
        }

        // Set loading state for this specific crew
        setSendingIndividualReminder(crewId);

        try {
            // Call the backend endpoint to update the reminder_sent_at field for this specific crew and notification
            const response = await fetch(`/api/circular/api/notifications/${notificationSrNo}/send-individual-reminder/`, { // Use your new endpoint
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
                alert(`Reminder sent successfully to ${targetCrewLabel}.`);
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
            const response = await fetch(`/api/circular/api/notifications/${srNoToDelete}/delete/`, {
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
        const csvDownloadUrl = `/api/circular/api/approved-notifications/download-csv/?${params}`;

        // Trigger the download by setting window.location.href
        // This is the standard way to trigger a file download from a link via JavaScript
        window.location.href = csvDownloadUrl;

        console.log("handleDownloadCSV: Download request sent to:", csvDownloadUrl);
    };
    // --- END NEW ---


    const handleSupersede = (srNoToSupersede) => {
        const notificationToSupersede = notifications.find(
            (notification) => notification.sr_no === srNoToSupersede,
        );
        if (!notificationToSupersede?.sr_no) {
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
        console.log(`🚀 handleSupersede: Preparing to supersede notification ${srNoToSupersede}`);

        try {
            localStorage.setItem('supersedingNotificationId', srNoToSupersede);
            console.log(`✅ handleSupersede: Stored supersedingNotificationId (${srNoToSupersede}) in localStorage`);

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

            console.log('✅ handleSupersede: Stored old notification details in localStorage for pre-filling.');
            window.location.href = redirectPath;
        } catch (storageError) {
            console.error(`❌ handleSupersede: Error preparing supersede data for ${srNoToSupersede}:`, storageError);
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
                        {filteredNotifications.length === 0 ? 0 : pageStartIndex + 1}
                        -
                        {Math.min(
                            pageStartIndex + APPROVED_NOTIFICATIONS_PER_PAGE,
                            filteredNotifications.length,
                        )}
                    </span>{" "}
                    of {filteredNotifications.length} approved notifications
                    {totalPages > 1 ? ` · Page ${safeCurrentPage} of ${totalPages}` : ""}
                </p>

                {filteredNotifications.length === 0 ? (
                    <div className="rounded-lg border border-dashed border-neutral-200 bg-white py-20 text-center text-neutral-500">
                        No notifications match your filters.
                    </div>
                ) : (
                    <div className="space-y-3">
                        {paginatedNotifications.map((n) => (
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
                                                        href={`${n.attachment_url}`}
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

                                            <WithPermission id="PSC_P_044">
                                                <button
                                                    type="button"
                                                    onClick={() => handleOpenResendModal(n)}
                                                    disabled={isResendSubmitting && resendNotification?.sr_no === n.sr_no}
                                                    process-id="PSC_P_044"
                                                    className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-warning-100 bg-warning-50 text-warning-700 shadow-sm transition-colors hover:bg-warning-100 disabled:cursor-not-allowed disabled:opacity-60"
                                                    aria-label={`Resend ${n.sr_no}`}
                                                    title={
                                                        isResendSubmitting && resendNotification?.sr_no === n.sr_no
                                                            ? `Repeating approval for ${n.sr_no}`
                                                            : `Repeat approval for ${n.sr_no}`
                                                    }
                                                >
                                                    <RefreshCcw size={14} className={isResendSubmitting && resendNotification?.sr_no === n.sr_no ? 'animate-spin' : ''} />
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
                                            <button
                                                type="button"
                                                onClick={() => openTitleModal(n.title || n.sr_no)}
                                                className="block w-full truncate text-left text-[17px] font-semibold leading-7 text-neutral-900 hover:text-primary-700"
                                                title="Click to view full title"
                                            >
                                                {n.title || n.sr_no}
                                            </button>
                                        </div>
                                    </div>

                                    {n.hashtags.length > 0 && (
                                        <div className="mb-3 flex flex-wrap gap-1.5">
                                            {n.hashtags.map((tag, index) => (
                                                <span
                                                    key={`${n.sr_no || n.id}-hashtag-${index}`}
                                                    className="inline-flex items-center rounded-full border border-primary-100 bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700"
                                                >
                                                    {tag.startsWith('#') ? tag : `#${tag}`}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                        {totalPages > 1 && (
                            <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                                    disabled={safeCurrentPage === 1}
                                    className="inline-flex h-10 min-w-10 items-center justify-center rounded-full bg-neutral-100 px-3 text-sm font-semibold text-neutral-700 transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-40"
                                    aria-label="Previous page"
                                >
                                    &lt;
                                </button>
                                {paginationPages.map((page) => (
                                    <button
                                        key={page}
                                        type="button"
                                        onClick={() => setCurrentPage(page)}
                                        className={`inline-flex h-10 min-w-10 items-center justify-center rounded-full px-3 text-sm font-semibold transition ${
                                            page === safeCurrentPage
                                                ? "bg-primary-600 text-white shadow-sm"
                                                : "bg-white text-neutral-900 underline underline-offset-4 hover:bg-neutral-100"
                                        }`}
                                        aria-current={page === safeCurrentPage ? "page" : undefined}
                                    >
                                        {page}
                                    </button>
                                ))}
                                <button
                                    type="button"
                                    onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                                    disabled={safeCurrentPage === totalPages}
                                    className="inline-flex h-10 min-w-10 items-center justify-center rounded-full bg-neutral-100 px-3 text-sm font-semibold text-neutral-700 transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-40"
                                    aria-label="Next page"
                                >
                                    &gt;
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {showResendModal && resendNotification && (
                    <div
                        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
                        onClick={closeResendModal}
                    >
                        <div
                            className="w-full max-w-5xl rounded-xl bg-white shadow-xl"
                            onClick={(event) => event.stopPropagation()}
                        >
                            <div className="flex items-center justify-between border-b border-neutral-200 px-6 py-4">
                                <div>
                                    <h2 className="text-lg font-semibold text-neutral-900">Repeat Approval</h2>
                                    <p className="text-sm text-neutral-500">{resendNotification.sr_no}</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={closeResendModal}
                                    className="rounded-md p-1 text-gray-500 transition hover:bg-neutral-100 hover:text-gray-700"
                                    aria-label="Close resend modal"
                                >
                                    &times;
                                </button>
                            </div>

                            <div className="max-h-[80vh] overflow-y-auto px-6 py-5">
                                {loadingResendOptions ? (
                                    <div className="py-12 text-center">
                                        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-b-2 border-sky-500" />
                                        <p className="mt-3 text-sm text-neutral-500">Loading vessels and ranks...</p>
                                    </div>
                                ) : (
                                    <div className="space-y-6">
                                        <div className="grid gap-6 lg:grid-cols-2">
                                            <div className="rounded-xl border border-neutral-200 p-4">
                                                <div className="mb-3 flex items-center justify-between">
                                                    <h3 className="text-sm font-semibold text-neutral-900">Select Vessels</h3>
                                                    <label className="inline-flex items-center gap-2 text-xs text-neutral-600">
                                                        <input
                                                            type="checkbox"
                                                            checked={resendVessels.length > 0 && resendVessels.every((vessel) => resendSelectedVesselIds.has(vessel.id))}
                                                            onChange={handleSelectAllResendVessels}
                                                        />
                                                        Select All
                                                    </label>
                                                </div>
                                                <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
                                                    {resendVessels.map((vessel) => (
                                                        <label
                                                            key={vessel.id}
                                                            className="flex items-center gap-3 rounded-lg border border-neutral-200 px-3 py-2 text-sm text-neutral-700"
                                                        >
                                                            <input
                                                                type="checkbox"
                                                                checked={resendSelectedVesselIds.has(vessel.id)}
                                                                onChange={() => handleResendVesselToggle(vessel.id)}
                                                            />
                                                            <span>
                                                                {vessel.vesselName || vessel.VesselName || vessel.vessel_name || vessel.name || vessel.id}
                                                                {vessel.vesselCode ? ` (${vessel.vesselCode})` : ""}
                                                            </span>
                                                        </label>
                                                    ))}
                                                </div>
                                            </div>

                                            <div className="rounded-xl border border-neutral-200 p-4">
                                                <div className="mb-3 flex items-center justify-between">
                                                    <h3 className="text-sm font-semibold text-neutral-900">Select Ranks</h3>
                                                    <label className="inline-flex items-center gap-2 text-xs text-neutral-600">
                                                        <input
                                                            type="checkbox"
                                                            checked={resendRanks.length > 0 && resendRanks.every((rank) => resendSelectedRankIds.has(rank.id))}
                                                            onChange={handleSelectAllResendRanks}
                                                        />
                                                        Select All
                                                    </label>
                                                </div>

                                                <div className="grid gap-4 md:grid-cols-2">
                                                    <div>
                                                        <div className="mb-2 flex items-center justify-between">
                                                            <h4 className="text-xs font-semibold uppercase tracking-wide text-sky-700">Deck</h4>
                                                            <label className="inline-flex items-center gap-2 text-[11px] text-neutral-600">
                                                                <input
                                                                    type="checkbox"
                                                                    checked={resendDeckRanks.length > 0 && resendDeckRanks.every((rank) => resendSelectedRankIds.has(rank.id))}
                                                                    onChange={() => toggleResendRankGroup(resendDeckRanks)}
                                                                />
                                                                Select All
                                                            </label>
                                                        </div>
                                                        <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
                                                            {resendDeckRanks.map((rank) => (
                                                                <label
                                                                    key={rank.id}
                                                                    className="flex items-center gap-3 rounded-lg border border-neutral-200 px-3 py-2 text-sm text-neutral-700"
                                                                >
                                                                    <input
                                                                        type="checkbox"
                                                                        checked={resendSelectedRankIds.has(rank.id)}
                                                                        onChange={() => handleResendRankToggle(rank.id)}
                                                                    />
                                                                    <span>{getCircularRankDisplayName(rank)}</span>
                                                                </label>
                                                            ))}
                                                        </div>
                                                    </div>

                                                    <div>
                                                        <div className="mb-2 flex items-center justify-between">
                                                            <h4 className="text-xs font-semibold uppercase tracking-wide text-sky-700">Technical</h4>
                                                            <label className="inline-flex items-center gap-2 text-[11px] text-neutral-600">
                                                                <input
                                                                    type="checkbox"
                                                                    checked={resendTechnicalRanks.length > 0 && resendTechnicalRanks.every((rank) => resendSelectedRankIds.has(rank.id))}
                                                                    onChange={() => toggleResendRankGroup(resendTechnicalRanks)}
                                                                />
                                                                Select All
                                                            </label>
                                                        </div>
                                                        <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
                                                            {resendTechnicalRanks.map((rank) => (
                                                                <label
                                                                    key={rank.id}
                                                                    className="flex items-center gap-3 rounded-lg border border-neutral-200 px-3 py-2 text-sm text-neutral-700"
                                                                >
                                                                    <input
                                                                        type="checkbox"
                                                                        checked={resendSelectedRankIds.has(rank.id)}
                                                                        onChange={() => handleResendRankToggle(rank.id)}
                                                                    />
                                                                    <span>{getCircularRankDisplayName(rank)}</span>
                                                                </label>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div>
                                            <label className="mb-2 block text-sm font-medium text-neutral-700">
                                                Approval Comment
                                            </label>
                                            <textarea
                                                value={resendComment}
                                                onChange={(event) => setResendComment(event.target.value)}
                                                rows={4}
                                                placeholder="Update the approval comment if needed..."
                                                className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm text-neutral-800 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="flex items-center justify-end gap-3 border-t border-neutral-200 px-6 py-4">
                                <button
                                    type="button"
                                    onClick={closeResendModal}
                                    disabled={isResendSubmitting}
                                    className="rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium text-neutral-700 transition hover:bg-neutral-50 disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="button"
                                    onClick={handleConfirmResendApproval}
                                    disabled={loadingResendOptions || isResendSubmitting}
                                    className="rounded-lg bg-sky-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-sky-800 disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                    {isResendSubmitting ? "Processing..." : "Repeat Approval"}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {expandedTitle && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={closeTitleModal}>
                        <div className="w-full max-w-2xl rounded-xl bg-white shadow-xl" onClick={(event) => event.stopPropagation()}>
                            <div className="flex items-center justify-between border-b border-neutral-200 px-6 py-4">
                                <h2 className="text-lg font-semibold text-neutral-900">Full Title</h2>
                                <button
                                    type="button"
                                    onClick={closeTitleModal}
                                    className="rounded-md p-1 text-gray-500 transition hover:bg-neutral-100 hover:text-gray-700"
                                    aria-label="Close full title modal"
                                >
                                    &times;
                                </button>
                            </div>
                            <div className="px-6 py-5 text-sm leading-7 text-neutral-800 break-words">
                                {expandedTitle}
                            </div>
                        </div>
                    </div>
                )}

                {/* --- NEW: View Seen Crews Modal --- */}

                {viewingSeenCrews && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                        <div className="w-full max-w-5xl max-h-[88vh] overflow-hidden rounded-xl bg-white shadow-xl">
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
                                            placeholder="Search rank, vessel, crew name or crew ID..."
                                            className="h-10 w-full rounded-lg border border-neutral-300 bg-white pl-10 pr-3 text-sm text-neutral-800 placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                                        />
                                    </div>
                                    <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                                        <div className="rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-3">
                                            <div className="text-xs uppercase tracking-wide text-neutral-500">Total Crew</div>
                                            <div className="mt-1 text-lg font-semibold text-neutral-900">{seenCrewStats.total}</div>
                                        </div>
                                        <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3">
                                            <div className="text-xs uppercase tracking-wide text-green-700">Seen</div>
                                            <div className="mt-1 text-lg font-semibold text-green-800">{seenCrewStats.seen}</div>
                                        </div>
                                        <div className="rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-3">
                                            <div className="text-xs uppercase tracking-wide text-neutral-500">Unread</div>
                                            <div className="mt-1 text-lg font-semibold text-neutral-900">{seenCrewStats.unread}</div>
                                        </div>
                                        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
                                            <div className="text-xs uppercase tracking-wide text-amber-700">Reminder Sent</div>
                                            <div className="mt-1 text-lg font-semibold text-amber-800">{seenCrewStats.reminded}</div>
                                        </div>
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
                                            <div className="space-y-3">
                                                <div className="hidden rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-neutral-500 md:grid md:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_minmax(0,1.2fr)_auto] md:gap-4">
                                                    <div>Crew</div>
                                                    <div>Rank / Vessel</div>
                                                    <div>Status</div>
                                                    <div className="text-right">Action</div>
                                                </div>
                                                {filteredSeenCrewsData.map((record, index) => (
                                                    <div
                                                        key={`${record.resolved_crew_id || record.crew_id || 'crew'}-${index}`}
                                                        className={`rounded-xl border p-4 ${
                                                            record.seen_at
                                                                ? 'border-green-200 bg-green-50/70'
                                                                : 'border-neutral-200 bg-white'
                                                        }`}
                                                    >
                                                        <div className="flex flex-col gap-4 md:grid md:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_minmax(0,1.2fr)_auto] md:items-center md:gap-4">
                                                            <div className="min-w-0">
                                                                <div className="font-semibold text-slate-900">{getCrewPrimaryLabel(record)}</div>
                                                                <div className="mt-1 text-xs text-slate-500">
                                                                    {record?.resolved_crew_id ? `Crew ID: ${record.resolved_crew_id}` : `Crew Ref: ${record?.crew_id || '-'}`}
                                                                </div>
                                                            </div>

                                                            <div className="min-w-0">
                                                                <div className="text-sm font-medium text-neutral-800">{record?.rank_name || 'Rank not available'}</div>
                                                                <div className="mt-1 text-xs text-neutral-500">{record?.vessel_name || 'Vessel not available'}</div>
                                                                <div className="mt-2">
                                                                    <span className="inline-flex rounded-full bg-sky-100 px-2.5 py-1 text-xs font-semibold text-sky-700">
                                                                        Status: {record?.crew_status_name || 'Unknown'}
                                                                    </span>
                                                                </div>
                                                            </div>

                                                            <div className="min-w-0">
                                                                <div className="flex flex-wrap items-center gap-2">
                                                                    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
                                                                        record.seen_at
                                                                            ? 'bg-green-100 text-green-700'
                                                                            : 'bg-neutral-100 text-neutral-600'
                                                                    }`}>
                                                                        {record.seen_at ? 'Seen' : 'Unread'}
                                                                    </span>
                                                                    {record.reminder_sent_at && (
                                                                        <span className="inline-flex rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700">
                                                                            Reminder Sent
                                                                        </span>
                                                                    )}
                                                                </div>
                                                                <div className="mt-2 space-y-1 text-xs text-neutral-500">
                                                                    <div>
                                                                        {record.seen_at
                                                                            ? `Seen at: ${formatCrewDateTime(record.seen_at)}`
                                                                            : 'Seen at: Not yet read'}
                                                                    </div>
                                                                    <div>
                                                                        {record.reminder_sent_at
                                                                            ? `Reminder at: ${formatCrewDateTime(record.reminder_sent_at)}`
                                                                            : 'Reminder at: Not sent'}
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            <div className="flex justify-start md:justify-end">
                                                                {!record.seen_at ? (
                                                                    <button
                                                                        onClick={() => handleSendIndividualReminder(viewingSeenCrews, record.crew_id, getCrewPrimaryLabel(record))}
                                                                        disabled={sendingIndividualReminder === record.crew_id}
                                                                        className={`inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${
                                                                            record.reminder_sent_at
                                                                                ? 'bg-warning-50 text-warning-700 hover:bg-warning-100'
                                                                                : 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                                                                        }`}
                                                                        title={
                                                                            sendingIndividualReminder === record.crew_id
                                                                                ? `Sending reminder to ${getCrewPrimaryLabel(record)}`
                                                                                : record.reminder_sent_at
                                                                                    ? `Resend reminder to ${getCrewPrimaryLabel(record)}`
                                                                                    : `Send reminder to ${getCrewPrimaryLabel(record)}`
                                                                        }
                                                                    >
                                                                        {record.reminder_sent_at ? (
                                                                            <BellRing size={14} className={sendingIndividualReminder === record.crew_id ? 'animate-pulse' : ''} />
                                                                        ) : (
                                                                            <Bell size={14} className={sendingIndividualReminder === record.crew_id ? 'animate-pulse' : ''} />
                                                                        )}
                                                                        {sendingIndividualReminder === record.crew_id
                                                                            ? 'Sending...'
                                                                            : record.reminder_sent_at
                                                                                ? 'Resend'
                                                                                : 'Remind'}
                                                                    </button>
                                                                ) : (
                                                                    <span className="text-xs font-medium text-green-700">No action needed</span>
                                                                )}
                                                            </div>
                                                        </div>
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
                                    Crew list is ordered by rank sequence where rank-level data is available.
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
