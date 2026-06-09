// Admin.jsx
import React, { useState, useEffect, useLayoutEffect, useRef, navigate } from 'react';
import '../../styles/circular/Officeuser.css';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/circular/ui/card';
import { Button } from '../../components/circular/ui/button';
import { Input } from '../../components/circular/ui/input';
import { Badge } from '../../components/circular/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/circular/ui/table';
import { WithPermission } from '../../utils/circular/permissionUtils';
import PageLayout from '../../components/layout/PageLayout';
import { useLocation, useNavigate } from 'react-router-dom';
import {useAuth} from '../../hooks/auth/useAuth';
import { useAuthStore } from '@/stores/auth-store';
import {
    resolveCircularDepartmentUiKey,
    resolveCircularMappedId,
    resolveCircularMappedName,
    resolveCircularMappedNames,
} from '../../utils/circular/supersede';
import {
    clearCircularDraftEditSession,
} from '../../utils/circular/draftSession';

const clearCircularPrefillStorage = () => {
    localStorage.removeItem('supersedingNotificationId');
    localStorage.removeItem('oldNotificationType');
    localStorage.removeItem('oldNotificationDept');
    localStorage.removeItem('oldNotificationCategory');
    localStorage.removeItem('oldNotificationPriority');
    localStorage.removeItem('oldNotificationSubCatNames');
    localStorage.removeItem('oldNotificationSecondSubCatNames');
    clearCircularDraftEditSession();
};

const isCircularFormReload = () => {
    if (typeof window === 'undefined') {
        return false;
    }

    const navigationEntries = window.performance?.getEntriesByType?.('navigation') || [];
    return navigationEntries[0]?.type === 'reload';
};

const Admin = ({ onNotificationSubmit }) => {

    const navigate = useNavigate();
    const location = useLocation();
    const draftRequestSrNoRef = useRef(null);
    // Form State



// Form State
    // ================= CORE DATA =================
    const [documentTypes, setDocumentTypes] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [priorities, setPriorities] = useState([]);
    const [subCategories, setSubCategories] = useState([]);
    const [secondSubCategories, setSecondSubCategories] = useState([]);

    // ================= ID MAPS =================
    const [deptToIdMap, setDeptToIdMap] = useState({});
    const [typeToIdMap, setTypeToIdMap] = useState({});
    const [priorityToIdMap, setPriorityToIdMap] = useState({});
    const [subCatToIdMap, setSubCatToIdMap] = useState({});
    const [secondSubCatToIdMap, setSecondSubCatToIdMap] = useState({});
    const [catToIdMap, setCatToIdMap] = useState({});

    // ================= SELECTION STATES =================
    const [selectedType, setSelectedType] = useState('');
    const [selectedMainOption, setSelectedMainOption] = useState(null);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [selectedSub1, setSelectedSub1] = useState(new Set());
    const [selectedSub2, setSelectedSub2] = useState(new Set());
    const [selectedSeverity, setSelectedSeverity] = useState('Critical');

    useLayoutEffect(() => {
        if (isCircularFormReload()) {
            clearCircularPrefillStorage();
        }
    }, []);

    useEffect(() => {
        const draftSrNoFromUrl = new URLSearchParams(location.search).get('draft_sr_no');
        if (!draftSrNoFromUrl) {
            return;
        }

        const normalizedDraftSrNo = String(draftSrNoFromUrl).trim();
        if (!normalizedDraftSrNo || draftRequestSrNoRef.current === normalizedDraftSrNo) {
            return;
        }

        draftRequestSrNoRef.current = normalizedDraftSrNo;
        setEditingDraftId(null);
        setEditingDraftSrNo(normalizedDraftSrNo);

        const fetchDraftForEditing = async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/circular/api/draft/${normalizedDraftSrNo}/`);

                if (!response.ok) {
                    throw new Error(`Failed to fetch draft: ${response.status} ${response.statusText}`);
                }

                const draftData = await response.json();
                setDraftPrefillData(draftData);
                navigate(location.pathname, { replace: true });
            } catch (error) {
                console.error('Failed to load draft for editing:', error);
                draftRequestSrNoRef.current = null;
                setEditingDraftId(null);
                setEditingDraftSrNo(null);
                setDraftPrefillData(null);
                navigate(location.pathname, { replace: true });
                alert(`Failed to load draft: ${error.message}`);
            }
        };

        fetchDraftForEditing();
    }, [location.pathname, location.search, navigate]);

    // ================= FORM DATA =================
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [files, setFiles] = useState([]);
    const [orientation, setOrientation] = useState('portrait');
    const [hashtags, setHashtags] = useState('');

    // ================= VESSEL =================
    const [showVesselPopup, setShowVesselPopup] = useState(false);
    const [vessels, setVessels] = useState([]);
    const [selectedVesselIds, setSelectedVesselIds] = useState(new Set());
    const [loadingVessels, setLoadingVessels] = useState(false);

    // ================= RANK =================
    const [showRankPopup, setShowRankPopup] = useState(false);
    const [allRanks, setAllRanks] = useState([]);
    const [ranksGroupedByDepartment, setRanksGroupedByDepartment] = useState({});
    const [selectedRankIds, setSelectedRankIds] = useState(new Set());
    const [loadingRanks, setLoadingRanks] = useState(false);

    // ================= MODALS & ACTIONS =================
    const [showCommentModal, setShowCommentModal] = useState(false);
    const [commentInput, setCommentInput] = useState('');
    const [currentAction, setCurrentAction] = useState('');
    const [currentSrNo, setCurrentSrNo] = useState('');
    const [approvingNotificationId, setApprovingNotificationId] = useState(null);

    // ================= SUBMISSIONS =================
    const [submittedRequests, setSubmittedRequests] = useState([]);
    const [viewingRequest, setViewingRequest] = useState(null);
    const [showPendingRequests, setShowPendingRequests] = useState(false);
    const [isLoadingNotifications, setIsLoadingNotifications] = useState(false);

    // ================= SUPERSEDING =================
    const [supersedingNotificationSrNo, setSupersedingNotificationSrNo] = useState(null);
    const [editingDraftId, setEditingDraftId] = useState(null);
    const [editingDraftSrNo, setEditingDraftSrNo] = useState(null);
    const [draftPrefillData, setDraftPrefillData] = useState(null);
    const [currentVesselIdsForComment, setCurrentVesselIdsForComment] = useState([]);

    const resolveEditingDraftContext = () => {
        const resolvedDraftId = String(
            editingDraftId ||
            draftPrefillData?.id ||
            ''
        ).trim().toLowerCase();
        const resolvedDraftSrNo = String(
            editingDraftSrNo ||
            draftPrefillData?.sr_no ||
            ''
        ).trim();

        return {
            draftId: resolvedDraftId || null,
            draftSrNo: resolvedDraftSrNo || null,
            isEditingDraftSession: Boolean(
                resolvedDraftId ||
                resolvedDraftSrNo ||
                draftPrefillData
            ),
        };
    };

    // ================= OLD NOTIFICATION =================
    const [oldNotificationType, setOldNotificationType] = useState(null);
    const [oldNotificationDeptId, setOldNotificationDeptId] = useState(null);
    const [oldNotificationCategory, setOldNotificationCategory] = useState(null);
    const [oldNotificationPriority, setOldNotificationPriority] = useState(null);
    const [oldNotificationSubCatNames, setOldNotificationSubCatNames] = useState([]);
    const [oldNotificationSecondSubCatNames, setOldNotificationSecondSubCatNames] = useState([]);
    const [isDocumentTypesLoading, setIsDocumentTypesLoading] = useState(true);




     // Get user data for header

    const {user} = useAuth();
    const userName = user?.display_name || user?.employee_id || user?.crew_id;

    // Logout handler
    const handleLogout = async () => {
        await useAuthStore.getState().logout();
        sessionStorage.clear();
        navigate('/login', { replace: true });
    };




    // --- NEW: Updated useEffect for fetching options and creating ID maps ---
    useEffect(() => {
        const fetchOptions = async () => {
            try {
                // --- Document Types ---
                const docRes = await fetch('http://localhost:8000/api/circular/api/document-types/');
                const docData = await docRes.json();
                console.log("Fetched Document Types:", docData);
                if (Array.isArray(docData)) {
                    // Create the map: { "Alert": "uuid1", "Circular": "uuid2", ... }
                    const typeMap = {};
                    docData.forEach(item => {
                        if (item && item[0] && item[1]) { // Assuming item = [id, name]
                            typeMap[item[1]] = item[0]; // name -> id
                        }
                    });
                    setTypeToIdMap(typeMap); // Store the map in state

                    // Set the list of names for the dropdown UI
                    const validDocTypes = docData.map(item => item[1]).filter(Boolean); // Extract the name (second element)
                    setDocumentTypes(validDocTypes);
                } else {
                    setTypeToIdMap({});
                    setDocumentTypes([]);
                }

                // Departments - Handle list of arrays
                const deptRes = await fetch('http://localhost:8000/api/circular/api/departments/');
                const deptData = await deptRes.json();
                // console.log("Fetched Departments:", deptData); // Log to verify structure

                // --- NEW: Create a mapping from department name to its ID (UUID) ---
                const deptNameToIdMap = {};
                if (Array.isArray(deptData)) {
                    deptData.forEach(item => {
                        if (item && item[0] && item[1]) { // Ensure the item array has both ID (index 0) and Name (index 1)
                            const id = item[0];     // The UUID string (e.g., '8949308c-aa8a-ee11-987c-7413ea3d6a70')
                            const name = item[1];   // The department name string (e.g., 'Deck')
                            deptNameToIdMap[name] = id; // Map name -> id
                        }
                    });
                }
                // Store the map in a state variable (define this state at the top of your component)
                setDeptToIdMap(deptNameToIdMap); // Assuming you have useState('deptToIdMap', {})
                // --- END NEW ---

                const normalizedDepts = Array.isArray(deptData)
                    ? deptData.map(item => item[1]).filter(Boolean) // Extract the second element (department_name) from each array
                    : [];
                setDepartments(normalizedDepts);


                // --- Priorities ---
                const prioRes = await fetch('http://localhost:8000/api/circular/api/priorities/');
                const prioData = await prioRes.json();
                console.log("Fetched Priorities:", prioData);
                if (Array.isArray(prioData)) {
                    const prioMap = {};
                    prioData.forEach(item => {
                        if (item && item[0] && item[1]) { // Assuming item = [id, name]
                            prioMap[item[1]] = item[0]; // name -> id
                        }
                    });
                    setPriorityToIdMap(prioMap); // Store the map in state

                    const normalizedPrios = prioData.map(item => item[1]).filter(Boolean); // Extract the name (second element)
                    setPriorities(normalizedPrios);
                } else {
                    setPriorityToIdMap({});
                    setPriorities([]);
                }

                // --- Sub-categories ---
                const subCatRes = await fetch('http://localhost:8000/api/circular/api/sub-categories/');
                const subCatData = await subCatRes.json();
                console.log("Fetched Sub-Categories:", subCatData);
                if (Array.isArray(subCatData)) {
                    const subCatMap = {};
                    subCatData.forEach(item => {
                        if (item && item.id && item.name) { // Assuming item = {id: "uuid", name: "Flag", ...}
                            subCatMap[item.name] = item.id; // name -> id
                        }
                    });
                    setSubCatToIdMap(subCatMap); // Store the map in state

                    const normalizedSubCats = subCatData.map(item => item.name).filter(Boolean); // Extract the name
                    setSubCategories(normalizedSubCats);
                } else {
                    setSubCatToIdMap({});
                    setSubCategories([]);
                }

                // --- Second Sub-categories (example, adjust structure as needed) ---
                // You might need a similar useEffect for second sub-categories if they are fetched dynamically based on department
                // const secondSubCatRes = await fetch('http://localhost:8000/api/circular/api/second-sub-categories/');
                // const secondSubCatData = await secondSubCatRes.json();
                // ... create map and set state ...

            } catch (err) {
                console.error('Failed to fetch options:', err);
                // Optionally, set error state or show an alert
                // setError('Failed to load form options.');
            }
        };

        fetchOptions();
    }, []); // Empty dependency array means this runs once on mount



    useEffect(() => {
        const fetchLookupData = async () => {
            try {
                const [typesRes, catsRes, subCatsRes, secondSubCatsRes, prioritiesRes] = await Promise.all([
                    fetch('http://localhost:8000/api/circular/api/document-types/'), // Example endpoint for MscType
                    // fetch('http://localhost:8000/api/circular/api/msc-categories/'), // Example endpoint for MscCategory
                    fetch('http://localhost:8000/api/circular/api/sub-categories/'), // Example endpoint for MscSubCat
                    fetch('http://localhost:8000/api/circular/api/second-sub-categories/'), // Example endpoint for Msc2ndSubCat
                    fetch('http://localhost:8000/api/circular/api/priorities/') // Example endpoint for MscPriority
                ]);

                const types = await typesRes.json();
                const cats = await catsRes.json();
                const subCats = await subCatsRes.json();
                const secondSubCats = await secondSubCatsRes.json();
                const priorities = await prioritiesRes.json();

                // Create maps from name to ID for easy lookup when submitting
                const typeMap = {};
                types.forEach(t => typeMap[t.name] = t.id);
                const catMap = {};
                cats.forEach(c => catMap[c.name] = c.id);
                const subCatMap = {};
                subCats.forEach(sc => subCatMap[sc.name] = sc.id);
                const secondSubCatMap = {};
                secondSubCats.forEach(scs => secondSubCatMap[scs.name] = scs.id);
                const priorityMap = {};
                priorities.forEach(p => priorityMap[p.name] = p.id);

                // Store these maps in component state or a global store if needed
                setTypeToIdMap(typeMap);
                setCatToIdMap(catMap);
                setSubCatToIdMap(subCatMap);
                setSecondSubCatToIdMap(secondSubCatMap);
                setPriorityToIdMap(priorityMap);

            } catch (err) {
                console.error("Failed to fetch lookup data:", err);
            }
        };

        fetchLookupData();
    }, []);


    const optionsLoaded =
        documentTypes.length > 0 &&
        departments.length > 0 &&
        priorities.length > 0 &&
        subCategories.length > 0 &&
        secondSubCategories.length > 0;


    useEffect(() => {
        const type = localStorage.getItem('oldNotificationType');
        const dept = localStorage.getItem('oldNotificationDept');

        if (type) {
            const resolvedType = resolveCircularMappedName(type, typeToIdMap);
            if (resolvedType) {
                setSelectedType(resolvedType.toLowerCase());
            }
        }

        if (dept) {
            const mappedDept = resolveCircularDepartmentUiKey(dept, deptToIdMap);
            if (mappedDept) {
                setSelectedMainOption(mappedDept);
            }
        }

    }, [typeToIdMap, deptToIdMap]);



    useEffect(() => {
        if (!selectedMainOption) return; // wait until dept is selected

        // const category = localStorage.getItem('oldNotificationCategory');
        const priority = localStorage.getItem('oldNotificationPriority');
        const sub1 = localStorage.getItem('oldNotificationSubCatNames');
        const sub2 = localStorage.getItem('oldNotificationSecondSubCatNames');

        // PRIORITY
        if (priority) {
            const resolvedPriority = resolveCircularMappedName(priority, priorityToIdMap);
            if (resolvedPriority) {
                setSelectedSeverity(resolvedPriority);
            }
        }

        // SUB1
        if (sub1) {
            const resolvedSubCategories = resolveCircularMappedNames(sub1, subCatToIdMap);
            setSelectedSub1(new Set(resolvedSubCategories));
        }

        // SUB2
        if (sub2) {
            const resolvedSecondSubCategories = resolveCircularMappedNames(sub2, secondSubCatToIdMap);
            setSelectedSub2(new Set(resolvedSecondSubCategories));
        }

    }, [priorityToIdMap, subCatToIdMap, secondSubCatToIdMap, selectedMainOption]);



    useEffect(() => {
        const handleRefresh = () => {
            console.log("ðŸ”„ Page refreshed â€” clearing supersede data");

            clearCircularPrefillStorage();
        };

        window.addEventListener("beforeunload", handleRefresh);

        return () => {
            window.removeEventListener("beforeunload", handleRefresh);
        };
    }, []);

       // Fetch submitted requests (only publish_status === 1)
        useEffect(() => {
            const fetchSubmittedRequests = async () => {
                try {
                    const res = await fetch('http://localhost:8000/api/circular/api/submitted/');
                    const data = await res.json();

                    const publishedRequests = Array.isArray(data)
                        ? data.filter(req => req.publish_status === 1)
                        : [];

                    const mappedRequests = publishedRequests.map(req => ({
                        id: req.sr_no || req.id,
                        type: req.msc_type?.toLowerCase() || 'alert',
                        priority: req.priority || 'Medium',
                        submitted: req.created_at

                            ? new Date(req.created_at).toLocaleString()
                            : 'â€”',
                        status: 'Pending',
                        created_by: req.created_by,
                        attachment_url: req.attachment_url,
                        details: {
                            mainOption: req.dept === 0 ? 'seq' : 'technical',
                            category: req.category || 'internal',
                            sub1: req.sub_category ? req.sub_category.split(', ') : [],
                            sub2: req.second_sub_category ? req.second_sub_category.split(', ') : [],
                            body: req.office_instructions || '',
                            files: req.attachment_url ? [req.attachment_url] : []
                        }
                    }));
                    // console.log("submit req", publishedRequests)
                    setSubmittedRequests(mappedRequests);
                } catch (err) {
                    console.error('Failed to fetch submitted requests:', err);
                }
            };

            fetchSubmittedRequests();
        }, []);




    // Fetch pending requests (publish_status === 1)
    useEffect(() => {
        const fetchPendingRequests = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/circular/api/submitted/');
                const data = await res.json();

                const pendingRequests = Array.isArray(data)
                    ? data.filter(req => req.publish_status === 1)
                    : [];

                const mappedRequests = pendingRequests.map(req => ({
                    id: req.id,
                    sr_no: req.sr_no,
                    type: req.msc_type?.toLowerCase() || 'alert',
                    priority: req.priority || 'Medium',
                    submitted: req.created_at
                        ? new Date(req.created_at).toLocaleString()
                        : 'â€”',
                    status: 'Pending',
                    created_by: req.created_by,
                    attachment_url: req.attachment_url,
                    details: {
                        mainOption: req.dept === 0 ? 'seq' : 'technical',
                        category: req.category || 'internal',
                        sub1: req.sub_category ? req.sub_category.split(', ') : [],
                        sub2: req.second_sub_category ? req.second_sub_category.split(', ') : [],
                        body: req.office_instructions || '',
                        files: []
                    }
                }));

                setSubmittedRequests(mappedRequests);
            } catch (err) {
                console.error('Failed to fetch pending requests:', err);
            }
        };

        fetchPendingRequests();
    }, []);



    // Fetch second sub-categories when department changes
    useEffect(() => {
        if (!selectedMainOption) {
            setSecondSubCategories([]); // Clear list if no department selected
            setSecondSubCatToIdMap({}); // Clear map if no department selected
            return;
        }

        const fetchSecondSub = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/circular/api/second-sub-categories/');
                const allData = await res.json();

                const targetDeptUuid = selectedMainOption === 'seq'
                    ? '8949308c-aa8a-ee11-987c-7413ea3d6a70'
                    : '8a49308c-aa8a-ee11-987c-7413ea3d6a70';

                if (Array.isArray(allData)) {
                    // Filter data for the selected department
                    const filteredData = allData.filter(item => {
                        if (!item || !item.department_id) return false;
                        return item.department_id.toLowerCase() === targetDeptUuid.toLowerCase();
                    });

                    // Create the map: { "Flag": "uuid1", "Maker": "uuid2", ... }
                    const map = {};
                    filteredData.forEach(item => {
                        if (item && item.id && item.name) { // Assuming item = {id: "uuid", name: "Flag", department_id: "uuid", ...}
                            map[item.name] = item.id; // name -> id
                        }
                    });
                    setSecondSubCatToIdMap(map); // Use the setter function here

                    // Set the list of names for the dropdown UI
                    const filteredNames = filteredData
                        .map(item => item.name)
                        .filter(Boolean);

                    setSecondSubCategories(filteredNames);
                } else {
                    setSecondSubCatToIdMap({});
                    setSecondSubCategories([]);
                }

            } catch (err) {
                console.error('Fetch error for second sub-categories:', err);
                setSecondSubCatToIdMap({});
                setSecondSubCategories([]);
            }
        };

        fetchSecondSub();
    }, [selectedMainOption]); // Re-run when selectedMainOption changes



    // --- NEW: Fetch Vessels when Popup Opens ---
    useEffect(() => {
        const fetchVessels = async () => {
            if (showVesselPopup) { // Only fetch when popup is shown
                console.log("Vessel Popup: Opening, fetching vessels...");
                setLoadingVessels(true);
                try {
                    const response = await fetch('http://localhost:8000/api/circular/api/vessels/'); // Use your vessel API endpoint
                    if (!response.ok) {
                        throw new Error(`Failed to fetch vessels: ${response.status} ${response.statusText}`);
                    }
                    const data = await response.json();
                    console.log("Vessel Popup: Fetched vessels:", data);
                    setVessels(data);
                } catch (err) {
                    console.error("Vessel Popup: Error fetching vessels:", err);
                    setVessels([]); // Set to empty array on error
                    alert(`Failed to load vessels: ${err.message}`);
                } finally {
                    setLoadingVessels(false);
                }
            }
        };

        fetchVessels();
    }, [showVesselPopup]); // Dependency: run when showVesselPopup changes
    // --- END NEW ---





    // --- NEW: Fetch All Ranks when Rank Popup Opens ---
    useEffect(() => {
        const fetchAllRanks = async () => {
            if (showRankPopup) { // Only fetch when rank popup is shown
                setLoadingRanks(true);
                try {
                    const response = await fetch('http://localhost:8000/api/circular/api/ranks/'); // Use the new endpoint
                    if (!response.ok) {
                        throw new Error(`Failed to fetch all ranks: ${response.status} ${response.statusText}`);
                    }
                    const data = await response.json();
                    console.log("Rank Popup: Fetched ALL ranks:", data);

                    // Group ranks by department for display
                    const groupedRanks = {};
                    data.forEach(rank => {
                        const dept = rank.department || 'Unknown Department'; // Use 'Unknown' if department is missing
                        if (!groupedRanks[dept]) {
                            groupedRanks[dept] = [];
                        }
                        groupedRanks[dept].push(rank);
                    });
                    // console.log("Rank Popup: Grouped ranks by department:", groupedRanks);

                    setAllRanks(data);
                    setRanksGroupedByDepartment(groupedRanks);

                } catch (err) {
                    console.error("Rank Popup: Error fetching all ranks:", err);
                    setAllRanks([]);
                    setRanksGroupedByDepartment({});
                    alert(`Failed to load ranks: ${err.message}`);
                } finally {
                    setLoadingRanks(false);
                }
            }
        };
        fetchAllRanks();
    }, [showRankPopup]); // Dependency: run when showRankPopup changes
    // END NEW





    // --- NEW: Effect to check for superseding notification ID on mount ---
    useEffect(() => {
        const storedSrNo = localStorage.getItem('supersedingNotificationId');
        if (storedSrNo) {
            console.log("Component mounted: Found supersedingNotificationId in localStorage:", storedSrNo);
            setSupersedingNotificationSrNo(storedSrNo); // Set the state variable
        } else {
            console.log("Component mounted: No supersedingNotificationId found in localStorage.");
            setSupersedingNotificationSrNo(null); // Ensure state is cleared if not present
        }
    }, []);
    // Empty dependency array means this runs once on mount
    // --- END NEW ---





    // --- NEW: Handler for Edit Pending Notification Button ---
    const handleEditPendingNotification = async (srNoToEdit) => {
        console.log("ðŸš€ handleEditPendingNotification: Edit clicked for notification SR No:", srNoToEdit);

        // 1. Fetch the notification details by its SR No
        console.log("handleEditPendingNotification: Fetching notification details for SR No:", srNoToEdit);
        try {
            const response = await fetch(`http://localhost:8000/api/circular/api/submitted/${srNoToEdit}/`); // Use your endpoint to get single notification details by SR No
            if (!response.ok) {
                throw new Error(`Failed to fetch notification details: ${response.status} ${response.statusText}`);
            }
            const notificationDetails = await response.json();
            console.log("handleEditPendingNotification: Retrieved notification details:", notificationDetails);

            // 2. Store the notification details in localStorage for the main form to use
            // This includes the SR No and the database ID (if needed for updates)
            localStorage.setItem('editingPendingNotificationData', JSON.stringify(notificationDetails));
            localStorage.setItem('editingPendingNotificationSrNo', notificationDetails.sr_no); // Store SR No
            localStorage.setItem('editingPendingNotificationId', notificationDetails.id); // Store DB ID (UUID)
            console.log("âœ… Stored editingPendingNotificationData, editingPendingNotificationSrNo, and editingPendingNotificationId in localStorage.");

            // 3. Navigate to the main create page to load the form with the data
            // This will trigger the main form component (Officeuser/Admin) to check localStorage
            // and populate the form fields.
            console.log("handleEditPendingNotification: Navigating to main form page to load pending notification data for editing.");
            navigate('/'); // Navigate to the main form page (assuming it's '/') // Adjust path if necessary

        } catch (detailsError) {
            console.error("handleEditPendingNotification: Error fetching notification details:", detailsError);
            alert(`âš ï¸ Could not fetch notification details for editing: ${detailsError.message}`);
        }
    };
    // --- END NEW ---

    // --- NEW: Updated handlePublishClick to set context ---
    const handlePublishClick = (e) => {
        e.preventDefault(); // Prevent default form submission for now
        console.log("Publish button clicked, triggering notification creation flow.");
        // Call handleConfirmPublish which will now handle the NEW submission flow
        handleConfirmPublish();
        // DO NOT setShowVesselPopup(true) here anymore
    };
    // --- END NEW ---


    // --- NEW: Handler for Vessel Checkbox Change ---
    const handleVesselCheckboxChange = (vesselId) => {
        console.log("Vessel Checkbox: Toggled for vessel ID:", vesselId);
        const newSelectedVesselIds = new Set(selectedVesselIds);
        if (newSelectedVesselIds.has(vesselId)) {
            newSelectedVesselIds.delete(vesselId);
            console.log("  - Removed vessel ID from selection.");
        } else {
            newSelectedVesselIds.add(vesselId);
            console.log("  - Added vessel ID to selection.");
        }
        setSelectedVesselIds(newSelectedVesselIds);
    };
    // --- END NEW ---



    // --- NEW: Handler for Rank Checkbox Change ---
    const handleRankCheckboxChange = (rankId) => {
        console.log("handleRankCheckboxChange: Toggled for rank ID:", rankId);
        const newSelectedRankIds = new Set(selectedRankIds);
        if (newSelectedRankIds.has(rankId)) {
            newSelectedRankIds.delete(rankId);
            console.log("  - Removed rank ID from selection.");
        } else {
            newSelectedRankIds.add(rankId);
            console.log("  - Added rank ID to selection.");
        }
        setSelectedRankIds(newSelectedRankIds);
    };
    // END NEW

    // --- NEW: Handler for Select All Ranks (for ALL ranks, regardless of department) ---
    const handleSelectAllRanksChange = () => {
        console.log("handleSelectAllRanksChange: Select All clicked. Current selected count:", selectedRankIds.size, "Total ranks:", allRanks.length);

        // If all ranks are currently selected, deselect all
        if (selectedRankIds.size === allRanks.length && allRanks.length > 0) {
            console.log("Deselecting all ranks.");
            setSelectedRankIds(new Set());
        } else {
            // Otherwise, select all ranks
            console.log("Selecting all ranks.");
            const allRankIds = new Set(allRanks.map(r => r.id));
            setSelectedRankIds(allRankIds);
        }
    };
    // END NEW

    // Inside your Admin component function

    // --- NEW: Handler for Select All DECK Ranks ---
    const handleSelectAllDeckRanksChange = () => {
        console.log("handleSelectAllDeckRanksChange: Select All DECK clicked. Current selected count:", selectedRankIds.size, "Total DECK ranks:", seqRanks.length);

        // Get the IDs of all DECK ranks
        const deckRankIds = new Set(seqRanks.map(r => r.id));

        // Create a new set for selected IDs
        let newSelectedRankIds = new Set(selectedRankIds); // Start with existing selections

        if (seqRanks.length > 0 && seqRanks.every(r => selectedRankIds.has(r.id))) {
            // If all DECK ranks are currently selected, deselect only the DECK ranks
            console.log("Deselecting all DECK ranks.");
            deckRankIds.forEach(id => newSelectedRankIds.delete(id));
        } else {
            // Otherwise, select all DECK ranks (add them to the set)
            console.log("Selecting all DECK ranks.");
            deckRankIds.forEach(id => newSelectedRankIds.add(id));
        }

        setSelectedRankIds(newSelectedRankIds);
    };
    // --- END NEW: Handler for Select All DECK Ranks ---

    // --- NEW: Handler for Select All ENGINE Ranks ---
    const handleSelectAllEngineRanksChange = () => {
        console.log("handleSelectAllEngineRanksChange: Select All ENGINE clicked. Current selected count:", selectedRankIds.size, "Total ENGINE ranks:", technicalRanks.length);

        // Get the IDs of all ENGINE ranks
        const engineRankIds = new Set(technicalRanks.map(r => r.id));

        // Create a new set for selected IDs
        let newSelectedRankIds = new Set(selectedRankIds); // Start with existing selections

        if (technicalRanks.length > 0 && technicalRanks.every(r => selectedRankIds.has(r.id))) {
            // If all ENGINE ranks are currently selected, deselect only the ENGINE ranks
            console.log("Deselecting all ENGINE ranks.");
            engineRankIds.forEach(id => newSelectedRankIds.delete(id));
        } else {
            // Otherwise, select all ENGINE ranks (add them to the set)
            console.log("Selecting all ENGINE ranks.");
            engineRankIds.forEach(id => newSelectedRankIds.add(id));
        }

        setSelectedRankIds(newSelectedRankIds);
    };
    // --- END NEW: Handler for Select All ENGINE Ranks ---


    const handleApproveReject = async (sr_no, action) => {
        console.log("ðŸš€ handleApproveReject: Start â†’ SR No:", sr_no, "Action:", action);

        const status = action === "approve" ? 2 : 3;
        setCurrentAction(action);
        setCurrentSrNo(sr_no);

        // Get current logged-in user (needed for publish_by / publish_on)
        const currentUser = user
        if (!currentUser || !currentUser.employee_id) {
            alert("You must be logged in to perform this action.");
            return;
        }

        /* ============================================================
           1ï¸âƒ£ APPROVE â†’ First fetch details â†’ then open vessel popup
           ============================================================ */
        if (action === "approve") {
            console.log("ðŸ“Œ Approve flow â†’ Fetching notification details...");

            try {
                const detailsResponse = await fetch(
                    `http://localhost:8000/api/circular/api/submitted/${sr_no}/`
                );

                if (!detailsResponse.ok) {
                    throw new Error(
                        `Failed fetching details: ${detailsResponse.status}`
                    );
                }

                const notificationDetails = await detailsResponse.json();
                console.log("ðŸ“„ Notification details:", notificationDetails);

                // Store SR No for later update
                localStorage.setItem(
                    "approvingNotificationSrNo",
                    notificationDetails.sr_no
                );

                // Store dept name for vessel fetching
                const deptName =
                    notificationDetails.dept === 0
                        ? "Deck"
                        : notificationDetails.dept === 1
                            ? "Engine"
                            : "Unknown";

                localStorage.setItem("approvingNotificationDept", deptName);

                console.log(
                    "ðŸ’¾ Stored dept + sr_no for popup vessel selection",
                    deptName
                );
            } catch (err) {
                console.error("âŒ Failed to fetch details for approval:", err);
                alert(
                    `Could not fetch details for approval.\nContinuing without vessel list.\n${err.message}`
                );
            }

            // Show vessel popup and stop here â€” final approval happens after popup confirm
            setShowVesselPopup(true);
            console.log("ðŸ“Œ Vessel popup opened.");
            return;
        }

        /* ============================================================
           2ï¸âƒ£ REJECT â†’ Show modal and wait for comment
           ============================================================ */
        setShowCommentModal(true);
        console.log("ðŸ“ Reject â†’ showing comment modal.");

        // The rest will run ONLY after comment submit, so we stop here
        // This prevents premature status update
        return;
    };

    /* ============================================================
       3ï¸âƒ£ FINAL APPROVAL / REJECTION API CALL
           CALL THIS AFTER COMMENT or AFTER VESSEL POPUP CONFIRM
       ============================================================ */

    const submitApprovalOrRejection = async (sr_no, action, comment, vesselIds = null) => {
        console.log("ðŸš€ Final submit:", { sr_no, action, comment, vesselIds });

        const currentUser = user
        const status = action === "approve" ? 2 : 3;

        const payload = {
            publish_status: status,
            publish_comment: comment || "",
        };

        if (action === "approve") {
            payload.published_by = currentUser.employee_id;
            payload.published_on = new Date().toISOString();
        }

        try {
            // ---- Update publish status ----
            const response = await fetch(
                `http://localhost:8000/api/circular/api/notifications/${sr_no}/update-status/`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                }
            );

            const result = await response.json();

            if (!response.ok) {
                alert(result.error || "Failed to update status");
                return;
            }

            alert(action === "approve" ? "Approved!" : "Rejected!");
            console.log("âœ… Status updated");

            /* ---------------------------------------------------
               ðŸ“§ EMAIL SENDING ONLY FOR APPROVAL
            --------------------------------------------------- */
            if (action === "approve" && vesselIds && vesselIds.length > 0) {
                console.log("ðŸ“§ Sending emails to vessels:", vesselIds);

                const emailPayload = {
                    notification_sr_no: sr_no,
                    vessel_ids: vesselIds,
                };

                const emailResponse = await fetch(
                    "http://localhost:8000/api/circular/api/notifications/send-emails/",
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(emailPayload),
                    }
                );

                const emailResult = await emailResponse.json();

                if (emailResponse.ok) {
                    console.log(
                        `ðŸ“¨ Emails sent to ${emailResult.emails_sent} vessels.`
                    );
                } else {
                    alert(`Approved, but email error: ${emailResult.error}`);
                }
            }

            // ---- Refresh pending list ----
            const res = await fetch("http://localhost:8000/api/circular/api/submitted/");
            const data = await res.json();

            const pendingRequests = (data || []).filter(
                (req) => req.publish_status === 1
            );

            const mappedRequests = pendingRequests.map((req) => ({
                id: req.id,
                sr_no: req.sr_no,
                type: req.msc_type?.toLowerCase() || "alert",
                priority: req.priority || "Medium",
                submitted: req.created_at
                    ? new Date(req.created_at).toLocaleString()
                    : "â€”",
                status: "Pending",
                created_by: req.created_by,
                attachment_url: req.attachment_url,
                details: {
                    mainOption: req.dept === 0 ? "seq" : "technical",
                    category: req.category || "internal",
                    sub1: req.sub_category ? req.sub_category.split(", ") : [],
                    sub2: req.second_sub_category
                        ? req.second_sub_category.split(", ")
                        : [],
                    body: req.office_instructions || "",
                    files: [],
                },
            }));

            setSubmittedRequests(mappedRequests);
        } catch (err) {
            console.error("ðŸ’¥ Network error:", err);
            alert("Network error occurred");
        }
    };



    // Replace the existing handleConfirmVesselSelectionForApproval with this
    const handleConfirmVesselSelectionForApproval = async () => {
        console.log("handleConfirmVesselSelectionForApproval: User confirmed vessel selection for approval.");
        const vesselIdsArray = Array.from(selectedVesselIds || []);
        console.log("handleConfirmVesselSelectionForApproval: Selected vessel IDs:", vesselIdsArray);

        // Get the original notification SR No from localStorage (set in handleApproveReject)
        const approvingNotificationSrNo = localStorage.getItem('approvingNotificationSrNo');
        console.log("handleConfirmVesselSelectionForApproval: approvingNotificationSrNo found:", approvingNotificationSrNo);

        if (!approvingNotificationSrNo) {
            // If creating a new notification, delegate to handleConfirmPublish as before
            console.log("No approvingNotificationSrNo found â€” treating this as a new submission.");
            await handleConfirmPublish();
            return;
        }

        if (vesselIdsArray.length === 0) {
            alert("Please select at least one vessel before confirming approval.");
            return;
        }

        // Store vessel IDs in state so comment modal / final handler can access them
        setCurrentVesselIdsForComment(vesselIdsArray);
        setCurrentAction('approve');
        setCurrentSrNo(approvingNotificationSrNo);

        // Show the comment modal. Do NOT submit server request here.
        setShowCommentModal(true);
        console.log("handleConfirmVesselSelectionForApproval: Opened comment modal â€” waiting for user to confirm comment.");
    };



    // Replaces the existing handleConfirmApprovalWithComment
    const handleConfirmApprovalWithComment = async () => {
        console.log("handleConfirmApprovalWithComment: Confirm clicked in comment modal.");

        const comment = commentInput || "";
        const notificationSrNoForComment = currentSrNo;
        const vesselIdsForComment = currentVesselIdsForComment || [];

        if (!notificationSrNoForComment) {
            console.error("handleConfirmApprovalWithComment: Missing notification SR No in state.");
            alert("An error occurred. Please try again.");
            return;
        }

        if (!Array.isArray(vesselIdsForComment) || vesselIdsForComment.length === 0) {
            console.error("handleConfirmApprovalWithComment: No vessel IDs available for approval.");
            alert("No vessels selected for approval. Please select at least one vessel.");
            return;
        }

        const currentUser = user
        if (!currentUser || !currentUser.employee_id) {
            alert('You must be logged in to approve notifications.');
            return;
        }

        const payload = {
            publish_status: 2,
            publish_comment: comment,
            published_by: currentUser.employee_id,
            published_on: new Date().toISOString(),
            vessel_ids: vesselIdsForComment
        };

        console.log("handleConfirmApprovalWithComment: Sending approval payload:", payload);

        try {
            const response = await fetch(
                `http://localhost:8000/api/circular/api/notifications/${notificationSrNoForComment}/update-status/`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                }
            );
            const result = await response.json();

            if (!response.ok) {
                alert(result.error || 'Failed to update status');
                console.error("Approval error:", result);
                return;
            }

            alert('Approved!');
            console.log("handleConfirmApprovalWithComment: Approval successful.");

            // Store vessel ids for email step (if you keep email separate)
            localStorage.setItem('selectedVesselIdsForNotification', JSON.stringify(vesselIdsForComment));

            // Send emails (optional: you already have this logic elsewhere â€” keep it here or delegate)
            try {
                const emailPayload = {
                    notification_sr_no: notificationSrNoForComment,
                    vessel_ids: vesselIdsForComment
                };
                const emailResponse = await fetch('http://localhost:8000/api/circular/api/notifications/send-emails/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(emailPayload),
                });
                const emailResult = await emailResponse.json();
                if (!emailResponse.ok) {
                    console.error("Email send error:", emailResult);
                    alert(`Approved, but failed to send emails: ${emailResult.error || 'Unknown error'}`);
                } else {
                    console.log("handleConfirmApprovalWithComment: Emails sent:", emailResult);
                }
            } catch (emailErr) {
                console.error("Email network error:", emailErr);
                alert('Approved, but email sending failed due to network error.');
            }

            // Close modal and open rank popup
            setShowCommentModal(false);
            setCommentInput('');
            setCurrentAction('');
            setCurrentSrNo('');
            setCurrentVesselIdsForComment([]);
            setShowRankPopup(true);

        } catch (err) {
            console.error("handleConfirmApprovalWithComment: Network error during approval:", err);
            alert('Network error during approval.');
        }
    };


    // New: Confirm reject with comment
    const handleConfirmRejectWithComment = async () => {
        console.log("handleConfirmRejectWithComment: Confirm reject clicked.");

        const comment = commentInput || "";
        const notificationSrNo = currentSrNo;
        if (!notificationSrNo) {
            console.error("handleConfirmRejectWithComment: Missing SR No in state.");
            alert("An error occurred. Please try again.");
            return;
        }

        const currentUser = user
        if (!currentUser || !currentUser.employee_id) {
            alert('You must be logged in to reject notifications.');
            return;
        }

        const payload = {
            publish_status: 3, // rejection
            publish_comment: comment
            // generally don't set published_by/on for reject unless required
        };

        console.log("handleConfirmRejectWithComment: Sending reject payload:", payload);

        try {
            const response = await fetch(
                `http://localhost:8000/api/circular/api/notifications/${notificationSrNo}/update-status/`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                }
            );

            const result = await response.json();
            if (!response.ok) {
                alert(result.error || 'Failed to update status');
                console.error("Reject error:", result);
                return;
            }

            alert('Rejected!');
            console.log("handleConfirmRejectWithComment: Rejection successful.");

            // Close modal and clear state
            setShowCommentModal(false);
            setCommentInput('');
            setCurrentAction('');
            setCurrentSrNo('');

            // Refresh list (reuse existing logic or call submitApprovalOrRejection/mapped refresh)
            // For simple approach, re-fetch submitted list:
            const res = await fetch('http://localhost:8000/api/circular/api/submitted/');
            const data = await res.json();
            const pendingRequests = Array.isArray(data) ? data.filter(req => req.publish_status === 1) : [];
            const mappedRequests = pendingRequests.map(req => ({
                id: req.id,
                sr_no: req.sr_no,
                type: req.msc_type?.toLowerCase() || 'alert',
                priority: req.priority || 'Medium',
                submitted: req.created_at ? new Date(req.created_at).toLocaleString() : 'â€”',
                status: 'Pending',
                created_by: req.created_by,
                attachment_url: req.attachment_url,
                details: {
                    mainOption: req.dept === 0 ? 'seq' : 'technical',
                    category: req.category || 'internal',
                    sub1: req.sub_category ? req.sub_category.split(', ') : [],
                    sub2: req.second_sub_category ? req.second_sub_category.split(', ') : [],
                    body: req.office_instructions || '',
                    files: []
                }
            }));
            setSubmittedRequests(mappedRequests);

        } catch (err) {
            console.error("handleConfirmRejectWithComment: Network error:", err);
            alert('Network error during rejection.');
        }
    };


    const handleConfirmRankSelection = async () => {
        console.log("handleConfirmRankSelection: User confirmed rank selection.");
        console.log("handleConfirmRankSelection: Selected rank IDs:", Array.from(selectedRankIds));

        // Get the notification ID and SR No from localStorage (set when approval started)
        const approvingNotificationId = localStorage.getItem('approvingNotificationId'); // This might be null if you are not storing it
        const approvingNotificationSrNo = localStorage.getItem('approvingNotificationSrNo');

        if (!approvingNotificationSrNo) { // You only need the SR No for the rank selection logic
            console.error("handleConfirmRankSelection: No notification SR No found in localStorage.");
            alert("An error occurred. Please try again.");
            return;
        }

        if (selectedRankIds.size === 0) {
            alert("Please select at least one rank before confirming.");
            return; // Stop if no ranks are selected
        }

        // Prepare payload for sending selected rank IDs to backend
        const rankPayload = {
            selected_rank_ids: Array.from(selectedRankIds), // Send the list of selected rank IDs
            notification_sr_no: approvingNotificationSrNo, // Send the notification SR No for context
            // Include other necessary data if the backend endpoint requires it
        };

        console.log("handleConfirmRankSelection: Prepared payload for rank-based crew notification:", rankPayload);

        try {
            // Send the selected rank IDs to the backend
            // You might need a new endpoint or modify an existing one to handle this
            // Example: Send to a new endpoint to link notification to ranks
            const response = await fetch(`http://localhost:8000/api/circular/api/notifications/${approvingNotificationSrNo}/link-ranks/`, { // Use a new endpoint
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(rankPayload), // Send the payload with selected ranks and notification context
            });

            const result = await response.json();

            if (response.ok) {
                alert('Notification approved, emails sent to vessels, and ranks selected successfully!');
                window.location.reload();

                //  CLEAR the approval flags from localStorage AFTER successful operation
                localStorage.removeItem('approvingNotificationSrNo'); // Clear SR No
                localStorage.removeItem('approvingNotificationDept'); // Clear Dept
                console.log("handleConfirmRankSelection: Cleared approvingNotificationSrNo and approvingNotificationDept from localStorage.");

                // Close the rank popup
                setShowRankPopup(false);

                // Clear selected ranks for next time
                setSelectedRankIds(new Set());

                // Clear form data if needed
                setTitle('');
                setBody('');
                setHashtags('');
                // ... reset other form fields as needed ...
                setFiles([]);

                // Refresh any relevant data in the parent component if necessary
                if (onNotificationSubmit) {
                    onNotificationSubmit(); // Notify parent to refresh the count
                }

            } else {
                alert('Error linking ranks: ' + (result.error || 'Failed to link'));
                console.error("handleConfirmRankSelection: Rank link response error:", result);
            }
        } catch (rankErr) {
            console.error("handleConfirmRankSelection: Network error during rank selection confirmation:", rankErr);
            alert('Network error during rank confirmation.');
        }
    };

    // --- NEW: Handler for Cancel Rank Selection ---
    const handleCancelRankSelection = () => {
        console.log("handleCancelRankSelection: User cancelled rank selection.");
        // Close the rank popup
        setShowRankPopup(false);
        // Optionally clear selected ranks if user cancels
        // setSelectedRankIds(new Set());
    };
    // --- END NEW ---


    // --- NEW: Updated handleFileChange with PDF validation ---
    const handleFileChange = (e) => {
        const newFiles = Array.from(e.target.files);
        console.log("handleFileChange: Received files:", newFiles);

        // Validate each file's type
        const validFiles = [];
        const invalidFiles = [];

        newFiles.forEach(file => {
            // Check if the file type is 'application/pdf'
            // Note: This relies on the browser's detection, which might not be 100% foolproof
            // for files with incorrect extensions but valid PDF content.
            // However, it's a good first-line check.
            if (file.type === 'application/pdf') {
                validFiles.push(file);
            } else {
                invalidFiles.push(file.name);
            }
        });

        if (invalidFiles.length > 0) {
            alert(`The following files are not PDFs and will be ignored: ${invalidFiles.join(', ')}`);
        }

        if (validFiles.length > 0) {
            // Add only the valid PDF files to the state
            setFiles(prevFiles => [...prevFiles, ...validFiles]);
            console.log("handleFileChange: Added valid PDF files to state:", validFiles);
        } else {
            console.log("handleFileChange: No valid PDF files were selected.");
        }
    };
    // --- END NEW ---


    //   const handleSubmit = async (e) => {
    //         e.preventDefault();

    //         if (!selectedType) {
    //             alert('Please select a document type (Alert, Circular, or Work Instruction).');
    //             return;
    //         }

    //         if (!selectedMainOption) {
    //             alert('Please select at least one: Seq or Technical.');
    //             return;
    //         }

    //         if (!selectedCategory) {
    //             alert('Please select a category: Internal or External.');
    //             return;
    //         }

    //         if (selectedSub1.size === 0) {
    //             alert('Please select at least one option under Sub-category.');
    //             return;
    //         }

    //         if (selectedCategory === 'internal' && selectedSub2.size === 0) {
    //             alert('Please select at least one option under the second subcategory.');
    //             return;
    //         }

    //         // Create FormData instead of JSON
    //         const formData = new FormData();
    //         formData.append('type', selectedType === 'alert' ? 'Alert' : selectedType === 'circular' ? 'Circular' : 'WorkInstruction');
    //         formData.append('department', selectedMainOption === 'seq' ? 0 : 1);
    //         formData.append('category', selectedCategory);
    //         formData.append('title', title); // Add title
    //         formData.append('body', body);
    //         formData.append('hashtags', hashtags);
    //         formData.append('print_type', orientation === 'portrait' ? 1 : 0);
    //         formData.append('publish_status', 2);
    //         formData.append('priority', selectedSeverity);
    //         formData.append('created_by', currentUser.employee_id);

    //         // Add sub-categories
    //         Array.from(selectedSub1).forEach(cat => formData.append('sub_cat', cat));
    //         Array.from(selectedSub2).forEach(cat => formData.append('second_sub_cat', cat));

    //         // Add files
    //         files.forEach(file => formData.append('attachment', file));

    //         try {
    //             const response = await fetch('http://localhost:8000/api/circular/api/notifications/', {
    //                 method: 'POST',
    //                 body: formData, // Not JSON!
    //             });

    //             const result = await response.json();
    //             if (response.ok) {
    //                 alert('Published!');
    //             } else {
    //                 alert('Error: ' + result.error);
    //             }
    //         } catch (err) {
    //             console.error(err);
    //             alert('Network error');
    //         }
    //     };


    const handleTypeClick = (typeName) => {
        setSelectedType(typeName); // e.g., 'alert', 'circular'
    };

    const handlePriorityClick = (priorityName) => {
        setSelectedSeverity(priorityName); // e.g., 'Critical', 'High', 'Medium', 'Low'
    };



    const handleSaveDraft = async (e) => {
        e.preventDefault(); // Prevent default form submission


        // --- Validation (Same as Submit, but less strict) ---
        if (!selectedType) {
            alert('Please select a document type (Alert, Circular, or Work Instruction).');
            return;
        }

        if (!selectedMainOption) {
            alert('Please select at least one: Seq or Technical.');
            return;
        }

        if (!selectedCategory) {
            alert('Please select a category: Internal or External.');
            return;
        }

        if (selectedSub1.size === 0) {
            alert('Please select at least one option under Sub-category.');
            return;
        }

        if (selectedCategory === 'internal' && selectedSub2.size === 0) {
            alert('Please select at least one option under the second subcategory.');
            return;
        }
        // --- End Validation ---

        // Get current user for created_by
        const currentUser = user
        if (!currentUser || !currentUser.employee_id) {
            alert('You must be logged in to save a draft.');
            return;
        }

        // --- Create FormData ---
        const formData = new FormData();

        // --- CHANGED: Use shared type lookup so spacing/casing variants still resolve ---
        const selectedTypeId = resolveCircularMappedId(selectedType, typeToIdMap);

        if (!selectedTypeId) {
            alert(`Document type ID not found for selection '${selectedType}'. Please try again.`);
            console.error("Missing ID for selected type:", selectedType, "Map:", typeToIdMap);
            return;
        }
        formData.append('type', selectedTypeId); // âœ… Send the UUID ID

        // Get the ID for 'department' using the map
        // Assuming selectedMainOption is 'seq' or 'technical'
        const deptNameForMap = selectedMainOption === 'seq' ? 'Deck' : 'Engine'; // Map frontend option to backend name
        const selectedDeptId = deptToIdMap[deptNameForMap];

        if (!selectedDeptId) {
            alert(`Department ID not found for selection '${deptNameForMap}'. Please try again.`);
            console.error("Missing ID for department key:", deptNameForMap, "Map:", deptToIdMap);
            return;
        }
        formData.append('department', selectedDeptId); // âœ… Send the UUID ID

        // For 'category', assuming it's still a string field (not a FK yet)
        formData.append('category', selectedCategory); // Send the name string

        // Get the ID for 'priority' using the map
        const selectedPriorityId = resolveCircularMappedId(selectedSeverity, priorityToIdMap);


        if (!selectedPriorityId) {
            alert(`Priority ID not found for selection '${selectedSeverity}'. Please try again.`);
            console.error("Missing ID for selected priority key:", selectedSeverity, "Map:", priorityToIdMap);
            return;
        }
        formData.append('priority', selectedPriorityId); // âœ… Send the UUID ID

        // Add other simple fields
        formData.append('title', title);
        formData.append('body', body);
        formData.append('hashtags', hashtags);
        formData.append('publish_status', 0); // âœ… Draft status
        formData.append('created_by', currentUser.employee_id);

        // Add sub-categories (send array of IDs using maps)
        Array.from(selectedSub1).forEach(name => {
            const id = subCatToIdMap[name]; // Look up the ID using the name
            if (id) {
                formData.append('sub_cat', id); // âœ… Append the UUID ID
            } else {
                console.warn(`handleSaveDraft: Could not find ID for sub-category name: ${name}`);
                // You might want to alert the user or handle this differently
                // For now, skip this item if no ID is found
                // alert(`Could not find ID for sub-category: ${name}`);
                // return; // Uncomment if you want to stop on error
            }
        });

        // Add second sub-categories (send array of IDs using maps)
        Array.from(selectedSub2).forEach(name => {
            const id = secondSubCatToIdMap[name]; // Look up the ID using the name
            if (id) {
                formData.append('second_sub_cat', id); // âœ… Append the UUID ID
            } else {
                console.warn(`handleSaveDraft: Could not find ID for second sub-category name: ${name}`);
                // You might want to alert the user or handle this differently
                // For now, skip this item if no ID is found
                // alert(`Could not find ID for second sub-category: ${name}`);
                // return; // Uncomment if you want to stop on error
            }
        });

        // Add files
        files.forEach(file => formData.append('attachment', file));
        // --- End FormData ---

        const {
            draftId: activeDraftId,
            draftSrNo: activeDraftSrNo,
            isEditingDraftSession,
        } = resolveEditingDraftContext();
        const draftUpdateUrl = activeDraftSrNo
            ? `http://localhost:8000/api/circular/api/draft/${activeDraftSrNo}/update/`
            : null;

        if (isEditingDraftSession && !draftUpdateUrl) {
            alert('Draft edit session was lost. Reopen the draft from the Drafts page.');
            return;
        }

        console.log("ðŸ“¤ Saving draft with FormData:", Object.fromEntries(formData.entries())); // Debug log

        try {
            const response = await fetch(
                draftUpdateUrl || 'http://localhost:8000/api/circular/api/notifications/', {
                method: 'POST',
                //  DO NOT set Content-Type â€” browser sets it automatically with boundary for FormData
                body: formData, //  Send formData, not JSON
            });

            const result = await response.json();
            if (response.ok) {
                alert(draftUpdateUrl ? 'Draft updated successfully!' : 'Draft saved successfully!');
                setEditingDraftId(null);
                setEditingDraftSrNo(null);
                setDraftPrefillData(null);
                clearCircularDraftEditSession();
                console.log("âœ… Draft saved with ID:", result.id);
                window.location.reload();
                // Optional: Reset form or redirect
                // resetForm(); // Implement this if you want to clear the form
            } else {
                alert('Error: ' + result.error);
            }
        } catch (err) {
            console.error('Network error during draft save:', err);
            alert('Network error');
        }
    };




    useEffect(() => {
        if (draftPrefillData) {
            try {
                const draft = draftPrefillData;
                console.log("=== LOADING DRAFT DATA ===");
                console.log("Full draft ", draft);

                // Set the body field using office_instructions
                if (draft.office_instructions !== undefined && draft.office_instructions !== null) {
                    setBody(draft.office_instructions);
                    console.log("Set body from office_instructions:", draft.office_instructions);
                } else {
                    console.log("No office_instructions field found in draft data or it was empty, setting body to empty string");
                    setBody('');
                }

                // Set other basic fields
                if (draft.title) {
                    setTitle(draft.title);
                    console.log("Set title:", draft.title);
                }

                if (draft.hashtags) {
                    setHashtags(draft.hashtags);
                    console.log("Set hashtags:", draft.hashtags);
                }

                // Set priority (selectedSeverity)
                if (draft.selectedSeverityForPreFill || draft.priority) {
                    const resolvedPriority = resolveCircularMappedName(
                        draft.selectedSeverityForPreFill || draft.priority,
                        priorityToIdMap,
                    );
                    if (resolvedPriority) {
                        setSelectedSeverity(resolvedPriority);
                        console.log("Set priority:", resolvedPriority);
                    }
                }

                // Set document type (msc_type -> selectedType)
                if (draft.selectedTypeForPreFill || draft.msc_type) {
                    const resolvedType = resolveCircularMappedName(
                        draft.selectedTypeForPreFill || draft.msc_type,
                        typeToIdMap,
                    );
                    if (resolvedType) {
                        const mappedType = String(resolvedType).toLowerCase();
                        setSelectedType(mappedType);
                        console.log("Set selectedType:", mappedType, "from msc_type:", draft.msc_type);
                    }
                }

                // Set department (dept -> selectedMainOption)
                if (draft.selectedMainOptionForPreFill || (draft.dept !== undefined && draft.dept !== null)) {
                    const mappedDept = resolveCircularDepartmentUiKey(
                        draft.selectedMainOptionForPreFill || draft.dept,
                        deptToIdMap,
                    );
                    if (mappedDept) {
                        setSelectedMainOption(mappedDept);
                        console.log("Set selectedMainOption:", mappedDept, "from dept:", draft.dept);
                    }
                }

                // Set category (category -> selectedCategory)
                if (draft.selectedCategoryForPreFill || draft.category) {
                    const mappedCategory = draft.selectedCategoryForPreFill || String(draft.category || '').toLowerCase();
                    setSelectedCategory(mappedCategory);
                    console.log("Set selectedCategory:", mappedCategory, "from category:", draft.category);
                }

                // Set sub-categories (sub_category -> selectedSub1)
                if (draft.selectedSub1ForPreFill || draft.sub_category) {
                    const resolvedSubCategories = resolveCircularMappedNames(
                        draft.selectedSub1ForPreFill || draft.sub_category,
                        subCatToIdMap,
                    );
                    const subCatSet = new Set(resolvedSubCategories);
                    setSelectedSub1(subCatSet);
                    console.log("Set selectedSub1:", Array.from(subCatSet), "from sub_category:", draft.sub_category);
                }

                // Set second sub-categories (second_sub_category -> selectedSub2)
                if (draft.selectedSub2ForPreFill || draft.second_sub_category) {
                    const resolvedSecondSubCategories = resolveCircularMappedNames(
                        draft.selectedSub2ForPreFill || draft.second_sub_category,
                        secondSubCatToIdMap,
                    );
                    const secondSubCatSet = new Set(resolvedSecondSubCategories);
                    setSelectedSub2(secondSubCatSet);
                    console.log("Set selectedSub2:", Array.from(secondSubCatSet), "from second_sub_category:", draft.second_sub_category);
                }
                console.log("=== DRAFT DATA LOADED SUCCESSFULLY ===");

            } catch (error) {
                console.error("Error parsing or loading draft ", error);
                console.error("Draft data that caused error:", draftPrefillData);
            }
        }
    }, [
        draftPrefillData,
        deptToIdMap,
        priorityToIdMap,
        secondSubCatToIdMap,
        subCatToIdMap,
        typeToIdMap,
    ]);




    const handleConfirmPublish = async () => {
        const selectedTypeId = resolveCircularMappedId(selectedType, typeToIdMap);

        if (!selectedTypeId) {
            alert("Document type ID not found. Please try again.");
            console.error("Missing ID for type:", selectedType, "Map:", typeToIdMap);
            return;
        }
        console.log("handleConfirmPublish: Confirm clicked. Checking for approval context...");
        // --- NEW: Check for Approval using SR No ---
        // Get the original notification SR No from localStorage (set when notification was loaded for approval)
        const approvingNotificationSrNo = localStorage.getItem('approvingNotificationSrNo');
        console.log("handleConfirmPublish: approvingNotificationSrNo (Serial Number) found:", approvingNotificationSrNo);
        // --- END NEW ---

        if (approvingNotificationSrNo) { // Check for SR No instead of ID
            // --- CONFIRM APPROVAL FLOW (Vessel Selection Popup during Approval) ---
            console.log("handleConfirmPublish: Executing vessel selection confirmation for approval of notification SR No:", approvingNotificationSrNo);

            // Get the selected vessel IDs from the state
            const selectedVesselIdsArray = Array.from(selectedVesselIds);
            console.log("handleConfirmPublish: Selected vessel IDs for approval:", selectedVesselIdsArray);

            if (selectedVesselIdsArray.length === 0) {
                alert("Please select at least one vessel before confirming approval.");
                return; // Stop if no vessels are selected
            }

            // Get current user for publisher info
            const currentUser = user
            if (!currentUser || !currentUser.employee_id) {
                alert('You must be logged in to approve notifications.');
                return;
            }

            // --- Prompt for Comment (for approval) ---
            let comment = null;
            const userChoice = window.confirm(`Do you want to add a comment for approval?`);
            if (userChoice) {
                comment = prompt("Please enter your comment:");
                if (comment === null || comment.trim() === "") {
                    comment = comment || ""; // Ensure it's a string if OK was clicked but empty
                }
                console.log("handleConfirmPublish: User entered comment for approval:", comment);
            } else {
                console.log("handleConfirmPublish: User skipped comment for approval.");
            }
            // --- End Prompt for Comment ---

            // Prepare payload for approval update with vessel IDs and comment
            const payload = {
                publish_status: 2, // Always 2 for approval
                publish_comment: comment,
                // Add publisher info
                published_by: currentUser.employee_id,
                published_on: new Date().toISOString(),
                // Add selected vessel IDs
                vessel_ids: selectedVesselIdsArray
            };

            console.log("handleConfirmPublish: Prepared payload for approval update:", payload);

            try {
                // --- CRITICAL: Use SR No in the URL ---
                // Send the request to the update-status endpoint for the specific notification being approved
                const response = await fetch(`http://localhost:8000/api/circular/api/notifications/${approvingNotificationSrNo}/update-status/`, { // Use SR No here
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload), // Send the payload with status, comment, publisher info, and vessel IDs
                });
                // --- END CRITICAL ---

                const result = await response.json();

                if (response.ok) {
                    alert('Approved!');

                    // Clear the approval flag from localStorage after successful approval
                    localStorage.removeItem('approvingNotificationSrNo'); // Clear the SR No (changed from ID)
                    console.log("handleConfirmPublish: Cleared approvingNotificationSrNo from localStorage.");

                    // Close the vessel popup
                    setShowVesselPopup(false);

                    // Clear selected vessels for next time (optional, might want to keep them for rank selection if needed)
                    // setSelectedVesselIds(new Set());

                    // --- NEW: Show Rank Selection Popup after vessel selection ---
                    console.log("handleConfirmPublish: Vessel selection confirmed. Now showing rank selection popup.");
                    // Fetch the department name based on the notification being approved
                    // You might need to fetch the notification details again to get its department
                    // Or store the department name when the approval process starts
                    // For now, let's assume you can get it from the notification details
                    // You can store it in localStorage when handleApproveReject is called
                    // Let's fetch the notification details again to get the department
                    try {
                        console.log("handleConfirmPublish: Fetching notification details again to get department for rank fetch...");
                        const detailsResponse = await fetch(`http://localhost:8000/api/circular/api/submitted/${approvingNotificationSrNo}/`); // Fetch using SR No
                        if (!detailsResponse.ok) {
                            throw new Error(`Failed to fetch notification details: ${detailsResponse.status} ${detailsResponse.statusText}`);
                        }
                        const notificationDetails = await detailsResponse.json();
                        console.log("handleConfirmPublish: Retrieved notification details for rank fetch:", notificationDetails);

                        // Determine department name for fetching ranks
                        // Assuming dept 0 is 'Deck' and dept 1 is 'Engine' based on your frontend logic
                        const deptNameForRanks = notificationDetails.dept === 0 ? 'Deck' : notificationDetails.dept === 1 ? 'Engine' : 'Unknown';
                        console.log("handleConfirmPublish: Mapped department for rank fetch:", deptNameForRanks);

                        if (deptNameForRanks === 'Unknown') {
                            console.warn("handleConfirmPublish: Could not determine department for notification SR No", approvingNotificationSrNo, ". Cannot fetch ranks for popup.");
                            alert("âš ï¸ Could not determine department for rank selection.");
                            // Continue without rank selection if department cannot be determined
                            // Optionally, you could store the department in localStorage when the approval starts
                            // and access it here without refetching.
                            // For now, let's just close the vessel popup and refresh.
                            if (onNotificationSubmit) {
                                onNotificationSubmit(); // Notify parent to refresh the count
                            }
                            return; // Exit the function early
                        }

                        // Store the department name in localStorage for the rank popup logic
                        localStorage.setItem('approvingNotificationDept', deptNameForRanks);
                        console.log("handleConfirmPublish: Stored approvingNotificationDept in localStorage:", deptNameForRanks);

                        // Show the rank selection popup
                        setShowRankPopup(true);
                        console.log("handleConfirmPublish: Rank selection popup displayed.");

                    } catch (detailsError) {
                        console.error("handleConfirmPublish: Error fetching notification details for rank selection popup:", detailsError);
                        alert(`Approved, but could not load ranks for selection: ${detailsError.message}`);
                        // Continue with refresh even if rank popup fails to load
                        if (onNotificationSubmit) {
                            onNotificationSubmit(); // Notify parent to refresh the count
                        }
                    }
                    // --- END NEW: Show Rank Selection Popup ---

                    // Refresh any relevant data in the parent component if necessary
                    // if (onNotificationSubmit) {
                    //     onNotificationSubmit(); // Notify parent to refresh the count
                    // }
                    // NOTE: We moved the refresh logic inside the rank selection block or after it,
                    // depending on if you want to refresh immediately after vessel approval
                    // or after the rank selection is also completed.

                } else {
                    alert('Error: ' + (result.error || 'Failed to update status'));
                    console.error("handleConfirmPublish: Approval response error:", result);
                }
            } catch (err) {
                console.error("handleConfirmPublish: Network error during approval:", err);
                alert('Network error');
            }

        } else {
            // --- CONFIRM NEW SUBMISSION FLOW (Publish, Save, then Show Vessel Popup) ---
            console.log("handleConfirmPublish: Executing creation flow for new notification, then showing vessel popup.");

            // Get current user for created_by and potentially published_by
            const currentUser = user
            if (!currentUser || !currentUser.employee_id) {
                alert('You must be logged in to submit a notification.');
                return;
            }

            // --- Validation (only for NEW submissions) ---
            if (!selectedType) {
                alert('Please select a document type (Alert, Circular, or Work Instruction).');
                return;
            }

            if (!selectedMainOption) {
                alert('Please select at least one: Seq or Technical.');
                return;
            }

            if (!selectedCategory) { // selectedCategory should hold the NAME from the dropdown
                alert('Please select a category: Internal or External.');
                return;
            }

            if (selectedSub1.size === 0) {
                alert('Please select at least one option under Sub-category.');
                return;
            }

            if (selectedCategory === 'internal' && selectedSub2.size === 0) {
                alert('Please select at least one option under the second subcategory.');
                return;
            }
            // --- End Validation ---

            // Create FormData
            const formData = new FormData();
            // --- CHANGED: Use ID maps for type, category, priority ---
            const selectedTypeId = resolveCircularMappedId(selectedType, typeToIdMap);
            // const selectedCategoryId = catToIdMap[selectedCategory]; // Use catToIdMap
            const selectedPriorityId = resolveCircularMappedId(selectedSeverity, priorityToIdMap);

            if (!selectedTypeId) {
                alert("Document type ID not found. Please try again.");
                console.error("Missing ID for type:", selectedType, "Map:", typeToIdMap);
                return;
            }
            if (!selectedPriorityId) {
                alert("Priority ID not found. Please try again.");
                console.error("Missing ID for priority:", selectedSeverity, "Map:", priorityToIdMap);
                return;
            }

            const departmentIdToSend = selectedMainOption === 'seq' ? deptToIdMap['Deck'] : deptToIdMap['Engine'];

            formData.append('type', selectedTypeId);
            formData.append('department', departmentIdToSend);
            formData.append('category', selectedCategory);// Send the ID
            formData.append('title', title);
            formData.append('body', body);
            formData.append('hashtags', hashtags);
            formData.append('publish_status', 2); // Publish directly
            formData.append('priority', selectedPriorityId); // Send the ID
            formData.append('created_by', currentUser.employee_id);
            // --- END CHANGED ---

            // Handle published_by and published_on for direct publish
            const publisherId = currentUser.employee_id; // Admin ID
            const publishedTimestamp = new Date().toISOString(); // Current time
            console.log("Admin is publishing directly. Setting publisher info:", {
                published_by: publisherId,
                published_on: publishedTimestamp
            });
            formData.append('published_by', publisherId);
            formData.append('published_on', publishedTimestamp);
            // --- End of published info handling ---

            // --- CHANGED: Send IDs for sub-categories ---
            selectedSub1.forEach(name => {
                const id = subCatToIdMap[name];
                if (id) {
                    formData.append('sub_cat', id); // Append the ID
                } else {
                    console.warn("Could not find ID for sub-category name:", name, "Map:", subCatToIdMap);
                }
            });
            Array.from(selectedSub2).forEach(name => {
                const id = secondSubCatToIdMap[name]; // Look up the ID using the name
                if (id) {
                    formData.append('second_sub_cat', id); // Append the ID
                }
                else {
                    console.warn("Could not find ID for second sub-category name:", name, "Map:", secondSubCatToIdMap);
                }
            });
            // --- END CHANGED ---

            // Add files
            files.forEach(file => formData.append('attachment', file));

            // DO NOT add vessel IDs here yet - they will be added via the update-status endpoint later
            // const newNotificationVesselIds = Array.from(selectedVesselIds); // Don't do this now

            try {
                console.log("handleConfirmPublish: Sending new notification creation request...");
                const response = await fetch('http://localhost:8000/api/circular/api/notifications/', {
                    method: 'POST',
                    body: formData, // Send the new data
                });

                const result = await response.json();
                if (response.ok) {
                    //  CRITICAL: Capture the SR No and ID from the backend response
                    const newNotificationSrNo = result.sr_no;
                    const newNotificationId = result.id;

                    if (newNotificationSrNo) {
                        console.log("âœ… New notification created successfully! SR No:", newNotificationSrNo);
                        // Store the new SR No in localStorage for subsequent use (e.g., vessel selection popup)
                        localStorage.setItem('approvingNotificationSrNo', newNotificationSrNo);
                        console.log("âœ… Stored new notification SR No in localStorage for vessel selection.");

                        // Also store the ID if you need it later
                        localStorage.setItem('approvingNotificationId', newNotificationId);
                        console.log("âœ… Stored new notification ID in localStorage.");

                        // NOW Show the Vessel Selection Popup
                        // Clear any previously selected vessels for this *new* notification
                        setSelectedVesselIds(new Set());
                        setShowVesselPopup(true); // Show the popup AFTER creation
                        console.log("handleConfirmPublish: Vessel selection popup displayed for newly created notification.");
                    } else {
                        console.error("âŒ Error: Backend did not return an SR No in the creation response:", result);
                        alert("Notification was saved, but an error occurred (SR No not returned).");
                    }

                    // Do NOT clear form data here, as user is now in vessel selection flow
                    // setTitle('');
                    // setBody('');
                    // setHashtags('');
                    // setFiles([]);

                    // Do NOT refresh here, as user is now in vessel selection flow
                    // if (onNotificationSubmit) {
                    //     onNotificationSubmit();
                    // }

                } else {
                    alert('Error creating notification: ' + (result.error || 'Unknown error'));
                    console.error("Create response error:", result);
                }
            } catch (err) {
                console.error('Network error during notification creation:', err);
                alert('Network error during creation.');
            }
            // End of CONFIRM NEW SUBMISSION FLOW (Publish, Save, then Show Vessel Popup)
        }
    };

    const handleSelectAllChange = () => {
        console.log("Select All checkbox clicked. Current selected count:", selectedVesselIds.size, "Total vessels:", vessels.length);

        // If all vessels are currently selected, deselect all
        if (selectedVesselIds.size === vessels.length && vessels.length > 0) {
            console.log("Deselecting all vessels.");
            setSelectedVesselIds(new Set());
        } else {
            // Otherwise, select all vessels
            console.log("Selecting all vessels.");
            const allVesselIds = new Set(vessels.map(v => v.id));
            setSelectedVesselIds(allVesselIds);
        }
    };

    // --- NEW: Handler for Cancel Publish (Close Popup) ---
    const handleCancelPublish = () => {
        console.log("Cancel Publish clicked, closing vessel selection popup.");
        setShowVesselPopup(false);
        // Optionally clear selected vessels if user cancels
        // setSelectedVesselIds(new Set());
    };
    // --- END NEW ---



    const handleSubmit = async (e) => {
        e.preventDefault();

        // --- NEW: Check for Supersede at the very beginning ---
        // Get the SR No of the OLD notification to be superseded from localStorage
        const supersedingOldSrNo = localStorage.getItem('supersedingNotificationId'); // Use consistent key
        console.log(".handleSubmit: Checking for superseding notification ID (OLD SR No):", supersedingOldSrNo);
        // --- END NEW ---

        // Get the original draft ID from localStorage (set when draft was loaded for editing)
        console.log("handleSubmit: editingDraftId (database ID) found:", editingDraftId);

        // Get current user for created_by

        const currentUser = user
        if (!currentUser || !currentUser.employee_id) {
            alert('You must be logged in to submit a notification.');
            return;
        }

        // --- CRITICAL CHANGE: Set initial publish status for Office User ---
        // Office Users submit for approval (status 1), not direct publish (status 2)
        const initialPublishStatus = 1; // Office User submits for approval
        console.log("handleSubmit: Office User submitting with initial publish_status:", initialPublishStatus);
        // --- END CRITICAL CHANGE ---

        if (!selectedType) {
            alert('Please select a document type (Alert, Circular, or Work Instruction).');
            return;
        }

        if (!selectedMainOption) {
            alert('Please select at least one: Seq or Technical.');
            return;
        }

        if (!selectedCategory) {
            alert('Please select a category: Internal or External.');
            return;
        }

        if (selectedSub1.size === 0) {
            alert('Please select at least one option under Sub-category.');
            return;
        }

        if (selectedCategory === 'internal' && selectedSub2.size === 0) {
            alert('Please select at least one option under the second subcategory.');
            return;
        }

        // --- NEW: Corrected Hashtag Validation ---
        const trimmedHashtags = hashtags.trim();

        // Rule 1: Check for spaces within individual hashtags
        // First, split the input by spaces to get potential segments
        const segments = trimmedHashtags.split(/\s+/).filter(segment => segment.length > 0);

        let isValidFormat = true;
        let hashtagCount = 0;

        // Iterate through each segment to validate
        for (let i = 0; i < segments.length; i++) {
            const segment = segments[i];
            // Check if the segment starts with '#'
            if (!segment.startsWith('#')) {
                isValidFormat = false;
                // Optional: Be more specific about the error
                alert(`Invalid hashtag format: '${segment}'. Each hashtag must start with '#'.`);
                break; // Stop checking further if one is invalid
            }
            // Check if there's only one '#' at the beginning
            // Count occurrences of '#'
            const hashCount = (segment.match(/#/g) || []).length;
            if (hashCount !== 1) {
                isValidFormat = false;
                // Optional: Alert for multiple hashes or misplaced hash
                alert(`Invalid hashtag format: '${segment}'. A hashtag must start with a single '#'.`);
                break;
            }
            // Check if there's actual content after the '#'
            if (segment.length <= 1) { // Only '#' or empty after '#'
                isValidFormat = false;
                // Optional: Alert for empty hashtag
                alert(`Invalid hashtag format: '${segment}'. A hashtag must have content after '#'.`);
                break;
            }
            // If it passes all checks, increment the valid hashtag count
            hashtagCount++;
        }

        // Rule 2: Enforce minimum of 5 valid hashtags
        if (trimmedHashtags && (!isValidFormat || hashtagCount < 5)) {
            if (!isValidFormat) {
                // alert('Invalid hashtag format. Each hashtag must start with a single \'#\' and contain no spaces within the tag itself (e.g., #tag1 #tag2).');
            } else if (hashtagCount < 5) {
                alert('Please enter at least 5 hashtags.');
            }
            return; // Stop submission if validation fails
        }

        // Optional: If the field is empty and you want it mandatory, uncomment below:
        if (hashtagCount === 0) {
            alert('Please enter at least 5 hashtags.');
            return;
        }
        // --- END NEW: Corrected Hashtag Validation ---
        const selectedTypeId = resolveCircularMappedId(selectedType, typeToIdMap);
        const selectedPriorityId = resolveCircularMappedId(selectedSeverity, priorityToIdMap);
        const departmentIdToSend = selectedMainOption === 'seq' ? deptToIdMap['Deck'] : deptToIdMap['Engine'];

        if (!selectedTypeId) {
            alert("Document type ID not found. Please try again.");
            return;
        }

        if (!selectedPriorityId) {
            alert("Priority ID not found. Please try again.");
            return;
        }
        // Create FormData
        const formData = new FormData();
        // formData.append('type', selectedType === 'alert' ? 'Alert' : selectedType === 'circular' ? 'Circular' : 'WorkInstruction');
        formData.append('type', selectedTypeId);
        formData.append('department', departmentIdToSend);
        formData.append('category', selectedCategory);
        formData.append('title', title);
        formData.append('body', body);
        formData.append('hashtags', hashtags);
        // CRITICAL: Use the initialPublishStatus determined for Office User (status 1)
        formData.append('publish_status', initialPublishStatus); // Set to 1 for pending approval
        formData.append('priority', selectedPriorityId);
        formData.append('created_by', currentUser.employee_id);

        // --- REMOVED: Handle published_by and published_on for direct publish ---
        // Office Users do NOT set published_by/on here. This is done by Admin during approval.
        // The logic for setting published_by/on based on initialPublishStatus === 2 is removed.
        // --- END REMOVED ---

        // --- NEW: Handle Supersede Data ---
        // If supersedingOldSrNo exists, send it to the backend
        // This tells create_notification to print "Supersedes ..." on the PDF
        if (supersedingOldSrNo) {
            console.log("handleSubmit: Adding supersede data for OLD SR No:", supersedingOldSrNo);
            // Append the SR No of the OLD notification to be superseded
            formData.append('superseded_id', supersedingOldSrNo); // Key change: send OLD SR No
        }
        // --- END NEW ---

        // Add Sub-Categories
        Array.from(selectedSub1).forEach(cat => {
            const id = subCatToIdMap[cat];
            if (id) {
                formData.append('sub_cat', id);
            }
        });
        Array.from(selectedSub2).forEach(cat => {
            const id = secondSubCatToIdMap[cat];
            if (id) {
                formData.append('second_sub_cat', id);
            }
        });

        // Add files
        files.forEach(file => formData.append('attachment', file));

        console.log("=== FormData Contents ===");
        for (let [key, value] of formData.entries()) {
            console.log(`${key}:`, value);
        }
        console.log("=========================");

        const {
            draftId: activeDraftId,
            draftSrNo: activeDraftSrNo,
            isEditingDraftSession,
        } = resolveEditingDraftContext();
        const draftUpdateUrl = activeDraftSrNo
            ? `http://localhost:8000/api/circular/api/draft/${activeDraftSrNo}/update/`
            : null;

        if (isEditingDraftSession && !draftUpdateUrl) {
            alert('Draft edit session was lost. Reopen the draft from the Drafts page.');
            return;
        }

        try {
            let response;
            let result;

            if (draftUpdateUrl) {
                // --- UPDATE PATH (Editing a draft) ---
                console.log("Editing draft with DATABASE ID:", activeDraftId);
                console.log("Editing draft with SR No:", activeDraftSrNo);
                console.log(`Sending request to update endpoint: ${draftUpdateUrl}`);

                // Send the request to the UPDATE endpoint using the specific DATABASE ID
                response = await fetch(draftUpdateUrl, {
                    method: 'POST',
                    body: formData, // Send the updated data (still pending approval)
                });

                result = await response.json();

                if (response.ok) {
                    alert('Draft updated and submitted for approval!');

                    // Clear the supersede flag from localStorage only if the update was successful
                    // and the notification was originally intended to supersede another one (supersedingOldSrNo was present at the start of the request).
                    if (supersedingOldSrNo) { // Check if the ID was present *before* the request was sent
                        localStorage.removeItem('supersedingNotificationId'); // Use consistent key
                        console.log("handleSubmit: Cleared supersedingNotificationId from localStorage after successful draft update.");
                    } else {
                        console.log("handleSubmit: No supersedingNotificationId was present initially, no need to clear.");
                    }
                    // --- END NEW ---

                    setEditingDraftId(null);
                    setEditingDraftSrNo(null);
                    setDraftPrefillData(null);
                    clearCircularDraftEditSession();
                    console.log("Cleared editingDraftId from localStorage");

                    // --- NEW: Refresh the page after successful submission/update ---
                    // This will clear all form state and localStorage flags like 'editingDraftId' and 'supersedingNotificationId'
                    window.location.reload();

                    // --- END NEW ---

                    // Clear form data if needed
                    setTitle('');
                    setBody('');
                    setHashtags('');
                    // ... reset other form fields as needed ...
                    setFiles([]);

                    // Refresh any relevant data in the parent component if necessary
                    if (onNotificationSubmit) {
                        onNotificationSubmit(); // Notify Parent To Refresh The Count
                    }

                } else {
                    alert('Error updating draft: ' + result.error);
                    console.error("Update response error:", result);
                }
                // End of UPDATE PATH - Execution Should Stop Here After Update
            } else {
                // --- CREATION PATH (New Notification - Could be superseding or standalone) ---
                console.log("Creating new notification");
                console.log("Sending request to create endpoint: /api/circular/api/notifications/");

                // The publish_status is Already Set To 1 Above

                response = await fetch('http://localhost:8000/api/circular/api/notifications/', {
                    method: 'POST',
                    body: formData, // Send the new data (pending approval), potentially including superseded_id
                });

                result = await response.json();

                if (response.ok) {
                    alert('Notification submitted for approval!');
                    window.location.reload();


                    // --- NEW: Clear Supersede Flag On Success (for new creations that were superseding) ---
                    // Clear the Supersede Flag from LocalStorage Regardless of OutCome
                    if (supersedingOldSrNo) {
                        localStorage.removeItem('supersedingNotificationId'); // Use consistent key
                        console.log("handleSubmit: Cleared supersedingNotificationId from localStorage.");
                    }
                    // --- END NEW ---

                    // Clear Form Data
                    setTitle('');
                    setBody('');
                    setHashtags('');
                    // ... reset other form fields as needed ...
                    setFiles([]);

                    // Refresh any relevant data in the parent component if necessary
                    if (onNotificationSubmit) {
                        onNotificationSubmit();
                    }

                    // --- START: Enhanced Crew List Display (only for NEW submissions) ---
                    // Note: This might be less relevant for pending submissions, but kept if desired.
                    console.log("=== Starting Crew List Display Process (New Submission - Pending) ===");
                    const deptNameForShipside = selectedMainOption === 'seq' ? 'Deck' : 'Engine';
                    console.log("Mapped Department for Crew List:", deptNameForShipside);

                    try {
                        // 1. Fetch the list of crews for the department
                        console.log("Fetching crews from Django API...");
                        const crewFetchUrl = `http://localhost:8000/api/circular/api/crews-by-department-and-vessel/?department=${deptNameForShipside}`;
                        console.log("Crew fetch URL:", crewFetchUrl);

                        const crewResponse = await fetch(crewFetchUrl);
                        console.log("Raw crew fetch response object:", crewResponse);

                        if (!crewResponse.ok) {
                            throw new Error(`Failed to fetch crews: ${crewResponse.status} ${crewResponse.statusText}`);
                        }

                        const crews = await crewResponse.json();
                        console.log("âœ… Successfully fetched crews:", crews);

                        // --- NEW: Display the crew list ---
                        if (Array.isArray(crews) && crews.length > 0) {
                            // Create a readable list of crew names/IDs
                            const crewList = crews.map(crew =>
                                crew.name || crew.employee_id || crew.CrewID || 'Unknown Crew'
                            ).join('\n');

                            // Show alert with crew list
                            // alert(`ðŸ”” Notification will be sent to:\n\n${crewList}`);

                            // Or log it to console in a nicely formatted way
                            console.log("ðŸ“‹ Crew List for Notification:");
                            crews.forEach((crew, index) => {
                                console.log(`  ${index + 1}. ${crew.name || crew.employee_id || crew.CrewID || 'Unknown'}`);
                            });
                        } else {
                            console.warn("âš ï¸ No crews found for department:", deptNameForShipside);
                            // alert("âš ï¸ No crew members found for this department.");
                        }
                        // --- END: Display the Crew list ---
                    } catch (crewListError) {
                        // Handle network errors or other issues during the crew list fetch
                        console.error("ðŸ’¥ Error during crew list fetch process:", crewListError);
                        // alert(`Notification saved, but there was an error fetching crew list: ${crewListError.message}`);
                    }
                    console.log("=== Finished Crew List Display Process ===");
                    // --- END: Enhanced Crew List Display ---

                } else {
                    alert('Error: ' + result.error);
                    console.error("Create response error:", result);
                }
                // End of creation path
            }

        } catch (err) {
            console.error('Network error during notification creation/update:', err);
            alert('Network error');
        }
    };






    // Toggle helpers
    const handleSub1Toggle = (item) => {
        setSelectedSub1(prev => {
            if (!(prev instanceof Set)) prev = new Set();
            const newSet = new Set(prev);
            newSet.has(item) ? newSet.delete(item) : newSet.add(item);
            return newSet;
        });
    };

    const handleSub2Toggle = (item) => {
        setSelectedSub2(prev => {
            if (!(prev instanceof Set)) prev = new Set();
            const newSet = new Set(prev);
            newSet.has(item) ? newSet.delete(item) : newSet.add(item);
            return newSet;
        });
    };

    // Dynamic options
    const sub1Options = subCategories;
    const sub2Options = secondSubCategories;
    const showCategorySelector = selectedMainOption !== null;

    // Render badges
    const renderStatusBadge = (status) => {
        if (status === 'Approved' || status === 2) {
            return <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">Approved</Badge>;
        } else if (status === 'Rejected' || status === 3) {
            return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">Rejected</Badge>;
        } else {
            return <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">Pending</Badge>;
        }
    };

    const renderTypeBadge = (type) => {
        if (type === 'alert') {
            return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">Alert</Badge>;
        } else if (type === 'circular') {
            return <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">Circular</Badge>;
        } else {
            return <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">Work Instruction</Badge>;
        }
    };

    const renderPriorityBadge = (priority) => {
        if (priority === 'Critical') {
            return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">Critical</Badge>;
        } else if (priority === 'High') {
            return <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">High</Badge>;
        } else if (priority === 'Medium') {
            return <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">Medium</Badge>;
        } else {
            return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">Low</Badge>;
        }
    };

    const seqRankNames = [
        'Master', 'Acting Master', 'Chief Engineer', 'Second Officer', 'Third Officer',
        'Deck Fitter', 'Deck Cadet', 'Bosun', 'Able Bodied Seaman',
        'Ordinary Seaman', 'Cook', 'Messman', 'Welder'
    ].map(name => name.toLowerCase()); // Normalize for comparison

    // Group the ranks based on their names
    // Use allRanks state here
    const seqRanks = allRanks.filter(rank => seqRankNames.includes((rank.rank_name || rank.name || '').toLowerCase()));
    const technicalRanks = allRanks.filter(rank => !seqRankNames.includes((rank.rank_name || rank.name || '').toLowerCase()));


    return (

     <div className="max-w-7xl mx-auto p-4 space-y-6 bg-sky-50 text-sky-700 ">
            {supersedingNotificationSrNo && (
                <div className="mb-4 p-3 bg-amber-100 border border-amber-200 rounded-lg">
                    <p className="text-sm text-amber-800 font-medium">
                        {/* Optional: Add an icon */}
                        {/* <Info size={14} className="inline mr-1" /> */}
                        You are superseding notification: <strong>{supersedingNotificationSrNo}</strong>
                    </p>
                </div>
            )}
            {/* Create Section */}
            <Card className="max-w-5xl mx-auto p-4 space-y-6 shadow-none border border-sky-100 rounded-xl ">
                <CardHeader className="pb-2">
                    <CardTitle className="text-lg font-semibold">Create Circular / Alert / WI</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                    <form id="AdminForm" onSubmit={handleConfirmPublish} className="space-y-6">
                        {/* Type Selector */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Document Type</label>
                                <div className="flex flex-wrap gap-2">
                                    {Array.isArray(documentTypes) && documentTypes.length > 0 ? (
                                        documentTypes.map((item) => {
                                            const typeName = typeof item === 'string'
                                                ? item
                                                : (item?.name || 'Unknown');
                                            const isSelected = selectedType === typeName.toLowerCase();
                                            return (
                                                <Button
                                                    key={typeof item === 'string' ? item : item.id || typeName}
                                                    type="button"
                                                    variant={isSelected ? "default" : "outline"}
                                                    size="sm"
                                                    onClick={() => setSelectedType(typeName.toLowerCase())}
                                                    className={`text-xs rounded-full ${isSelected ? 'bg-blue-200 text-blue-800 border-blue-300' : ''}`}
                                                >
                                                    {typeName}
                                                </Button>
                                            );
                                        })
                                    ) : (
                                        <span className="text-sm text-gray-500">Loading types...</span>
                                    )}
                                </div>
                            </div>

                            {/* Seq / Technical Selector */}
                            {selectedType && (
                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-700">Department</label>
                                    <div className="flex flex-wrap gap-2">
                                        {departments.map((deptName) => {
                                            const uiLabel = deptName === 'Deck' ? 'SEQ' : deptName === 'Engine' ? 'Technical' : deptName;
                                            const uiKey = deptName === 'Deck' ? 'seq' : deptName === 'Engine' ? 'technical' : deptName.toLowerCase();

                                            return (
                                                <Button
                                                    key={deptName}
                                                    type="button"
                                                    variant={selectedMainOption === uiKey ? "default" : "outline"}
                                                    size="sm"
                                                    onClick={() => setSelectedMainOption(uiKey)}
                                                    className={`text-xs rounded-full ${selectedMainOption === uiKey ? 'bg-blue-100 text-blue-800 border-blue-300' : ''}`}
                                                >
                                                    {uiLabel}
                                                </Button>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}

                            {/* Category: Internal / External */}
                            {showCategorySelector && (
                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-700">Scope</label>
                                    <div className="flex flex-wrap gap-2">
                                        <Button
                                            type="button"
                                            variant={selectedCategory === 'internal' ? "default" : "outline"}
                                            size="sm"
                                            onClick={() => setSelectedCategory('internal')}
                                            className={`text-xs ${selectedCategory === 'internal' ? 'bg-sky-100 text-sky-800 border-sky-300' : ''}`}
                                        >
                                            Internal
                                        </Button>
                                        <Button
                                            type="button"
                                            variant={selectedCategory === 'external' ? "default" : "outline"}
                                            size="sm"
                                            onClick={() => setSelectedCategory('external')}
                                            className={`text-xs ${selectedCategory === 'external' ? 'bg-sky-100 text-sky-800 border-sky-300' : ''}`}
                                        >
                                            External
                                        </Button>
                                    </div>
                                </div>
                            )}

                            {/* Subcategory 1: Always visible (compulsory) */}
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Sub-category</label>
                                <div className="flex flex-wrap gap-2">
                                    {sub1Options.map((opt) => {
                                        const isSelected = selectedSub1 instanceof Set && selectedSub1.has(opt);
                                        return (
                                            <Button
                                                key={opt}
                                                type="button"
                                                variant={isSelected ? "default" : "outline"}
                                                size="sm"
                                                onClick={() => handleSub1Toggle(opt)}
                                                className={`text-xs ${isSelected ? 'bg-blue-100 text-blue-800 border-blue-300' : ''}`}
                                            >
                                                {opt}
                                            </Button>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Subcategory 2: Only visible when category is internal */}
                            {selectedCategory === 'internal' && selectedMainOption && (
                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-700 ">
                                        Second sub-category:
                                    </label>
                                    <div className="flex flex-wrap gap-2">
                                        {sub2Options.map((opt) => {
                                            const isSelected = selectedSub2 instanceof Set && selectedSub2.has(opt);
                                            return (
                                                <Button
                                                    key={opt}
                                                    type="button"
                                                    variant={isSelected ? "default" : "outline"}
                                                    size="sm"
                                                    onClick={() => handleSub2Toggle(opt)}
                                                    className={`text-xs ${isSelected ? 'bg-blue-100 text-blue-800 border-blue-300' : ''}`}
                                                >
                                                    {opt}
                                                </Button>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}

                            {/* Priority */}
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">Priority</label>
                                <div className="flex flex-wrap gap-2">
                                    {priorities.map((prio) => (
                                        <Button
                                            key={prio}
                                            type="button"
                                            variant={selectedSeverity === prio ? "default" : "outline"}
                                            size="sm"
                                            onClick={() => setSelectedSeverity(prio)}
                                            className={`text-xs rounded-full ${selectedSeverity === prio
                                                ? prio === 'Critical'
                                                    ? 'bg-red-200 text-red-800 border-red-300'
                                                    : prio === 'High'
                                                        ? 'bg-amber-200 text-amber-800 border-amber-300'
                                                        : prio === 'Medium'
                                                            ? 'bg-blue-200 text-blue-800 border-blue-300'
                                                            : 'bg-green-200 text-green-800 border-green-300'
                                                : ''
                                                }`}
                                        >
                                            {prio}
                                        </Button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Title */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Title</label>
                            <Input
                                placeholder="Title"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                            />
                        </div>

                        {/* Body */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Body / Instructions</label>
                            <textarea
                                placeholder="Instructions in Details"
                                className="w-full rounded-md border border-sky-300 p-3 text-sm min-h-[140px]"
                                value={body}
                                onChange={(e) => setBody(e.target.value)}
                                required
                            />
                        </div>



                        {/* Hashtags */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">
                                Hashtags
                            </label>
                            <Input
                                placeholder="Enter hashtags separated by spaces"
                                value={hashtags}
                                onChange={(e) => setHashtags(e.target.value)}
                            />
                        </div>

                        {/* Attachments */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">Attachments</label>
                            <label className="flex items-center gap-2 w-fit px-3 py-2 border border-sky-200 rounded-md bg-sky-50 hover:bg-sky-100 cursor-pointer text-sm">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M20 14.66V20a2 2 0 01-2 2H6a2 2 0 01-2-2v-5.34"></path>
                                    <path d="M12 14l-4-4m4 4l4-4"></path>
                                    <path d="M12 14v6"></path>
                                </svg>
                                <span>Add filesâ€¦</span>
                                <input type="file" className="hidden" multiple onChange={handleFileChange} accept=".pdf" />
                            </label>
                            {files.length > 0 && (
                                <div className="flex flex-wrap gap-2 mt-2 text-xs text-slate-600">
                                    {Array.from(files).map((file, i) => (
                                        <span key={i} className="px-2 py-1 rounded-full border border-sky-200 bg-white">
                                            {file.name} ({(file.size / 1024).toFixed(1)} KB)
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>



                        {/* --- NEW: Vessel Selection Popup Modal --- */}
                        {showVesselPopup && (


                            <div className="fixed inset-0 backdrop-blur-sm bg-black/20 flex items-center justify-center z-50">

                                <div className="bg-white rounded-xl shadow-xl w-full max-w-md max-h-[80vh] overflow-y-auto">
                                    <div className="p-6">
                                        <h2 className="text-xl font-bold text-gray-800 mb-4">Select Vessels</h2>

                                        {/* Vessel List */}
                                        {loadingVessels ? (
                                            <div className="text-center py-4">
                                                <p className="text-gray-500">Loading vessels...</p>
                                            </div>
                                        ) : vessels.length > 0 ? (
                                            <div className="space-y-3 max-h-60 overflow-y-auto pr-2">
                                                {/* Select All Checkbox */}
                                                <div className="grid grid-cols-[20px_1fr] items-center gap-3 sticky top-0 bg-white py-2 z-10 border-b border-gray-200">

                                                    <input
                                                        type="checkbox"
                                                        id="select-all-vessels"
                                                        // Checked if all vessels are selected (and there are vessels)
                                                        checked={vessels.length > 0 && vessels.every(v => selectedVesselIds.has(v.id))}
                                                        // Indeterminate if some but not all are selected
                                                        ref={(input) => {
                                                            if (input) {
                                                                input.indeterminate = selectedVesselIds.size > 0 && selectedVesselIds.size < vessels.length;
                                                            }
                                                        }}
                                                        onChange={handleSelectAllChange} // New handler
                                                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                                                    />
                                                    <label
                                                        htmlFor="select-all-vessels"
                                                        className="text-sm font-medium text-gray-700"

                                                    >
                                                        Select All
                                                    </label>
                                                </div>

                                                {/* Individual Vessel Checkboxes */}
                                                {vessels.map((vessel) => (
                                                    <div key={vessel.id} className="grid grid-cols-[20px_1fr] items-center gap-3 pl-4"> {/* Added pl-6 to indent individual items under Select All */}
                                                        <input
                                                            type="checkbox"
                                                            id={`vessel-${vessel.id}`}
                                                            checked={selectedVesselIds.has(vessel.id)}
                                                            onChange={() => handleVesselCheckboxChange(vessel.id)}
                                                            className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                                                        />
                                                        <label
                                                            htmlFor={`vessel-${vessel.id}`}
                                                            className="text-sm text-gray-700 leading-tight"

                                                        >
                                                            {vessel.vesselName} ({vessel.vesselCode})
                                                        </label>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="text-center py-4">
                                                <p className="text-gray-500">No vessels found.</p>
                                            </div>
                                        )}


                                        {/* Action Buttons */}
                                        <div className="flex justify-end space-x-3 mt-6">
                                            <button
                                                type="button"
                                                onClick={handleCancelPublish} // Use existing handler
                                                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg text-sm font-medium hover:bg-gray-300 transition"
                                            >
                                                Cancel
                                            </button>
                                            <button
                                                type="button"
                                                onClick={handleConfirmVesselSelectionForApproval} // Call the new handler
                                                disabled={selectedVesselIds.size === 0} // Disable if no vessels selected
                                                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${selectedVesselIds.size === 0
                                                    ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                                                    : 'bg-sky-700 hover:bg-sky-800 text-white'
                                                    }`}
                                            >
                                                Confirm Approval
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>

                        )}


                        {/* --- NEW: Comment Modal --- */}
                        {showCommentModal && (
                            <div className="fixed inset-0 backdrop-blur-sm bg-black/20 flex items-center justify-center z-50">
                                <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
                                    <div className="p-6">
                                        <h3 className="text-lg font-semibold text-gray-800 mb-2">Add Comment</h3>
                                        <p className="text-sm text-gray-600 mb-4">
                                            Do you want to add a comment for <strong>{currentAction === 'approve' ? 'approval' : 'rejection'}</strong> of notification <strong>{currentSrNo}</strong>?
                                        </p>
                                        <textarea
                                            value={commentInput}
                                            onChange={(e) => setCommentInput(e.target.value)}
                                            placeholder="Enter your comment here..."
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-sky-400 focus:border-sky-400"
                                            rows="4" // Adjust number of visible rows as needed
                                        />
                                        <div className="flex justify-end space-x-3 mt-4">
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    setShowCommentModal(false);
                                                    setCommentInput(''); // Clear input when closing
                                                    setCurrentAction(''); // Clear action
                                                    setCurrentSrNo(''); // Clear SR No
                                                }}
                                                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg text-sm font-medium hover:bg-gray-300 transition"
                                            >
                                                Cancel
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    if (currentAction === 'approve') {
                                                        handleConfirmApprovalWithComment();
                                                    } else if (currentAction === 'reject') {
                                                        handleConfirmRejectWithComment();
                                                    } else {
                                                        console.error("Unknown action for comment confirm:", currentAction);
                                                        alert("Unknown action. Please try again.");
                                                    }
                                                }}
                                                className="px-4 py-2 bg-sky-700 text-white rounded-lg text-sm font-medium hover:bg-sky-800 transition"
                                            >
                                                Confirm {currentAction === 'approve' ? 'Approve' : 'Reject'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                        {/* --- END NEW: Comment Modal --- */}

                        {/* --- NEW: Rank Selection Popup Modal (Grouped by Department) --- */}
                        {showRankPopup && (
                           <div className="fixed inset-0 backdrop-blur-sm bg-black/20 flex items-center justify-center z-50">
                                <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto"> {/* Increased width for two columns */}
                                    <div className="p-6">
                                        <h2 className="text-xl font-bold text-gray-800 mb-4">Select Ranks</h2>

                                        {/* Select All Checkbox (for ALL ranks) */}
                                        <div className="grid grid-cols-[20px_1fr] items-center gap-3 mb-3">

                                            <input
                                                type="checkbox"
                                                id="select-all-ranks"
                                                checked={allRanks.length > 0 && allRanks.every(r => selectedRankIds.has(r.id))}
                                                ref={(input) => {
                                                    if (input) {
                                                        input.indeterminate = selectedRankIds.size > 0 && selectedRankIds.size < allRanks.length;
                                                    }
                                                }}
                                                onChange={handleSelectAllRanksChange}
                                                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                                            />
                                            <label htmlFor="select-all-ranks" className="text-sm font-medium text-gray-700"
>
                                                Select All Ranks
                                            </label>
                                        </div>

                                        {/* --- NEW: Horizontal Layout for SEQ and TECHNICAL Ranks --- */}
                                        {/* Use flexbox to arrange the two groups side by side */}
                                        {loadingRanks ? (
                                            <div className="text-center py-4">
                                                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-sky-500 mx-auto"></div>
                                                <p className="text-gray-500 mt-2">Loading ranks...</p>
                                            </div>
                                        ) : (
                                            <div className="flex flex-col md:flex-row gap-6"> {/* Use flex-col on small screens, flex-row on medium and larger screens */}
                                                {/* DECK Ranks Section */}
                                                {seqRanks.length > 0 && (
                                                    <div className="flex-1 mb-4 md:mb-0"> {/* Use flex-1 to take up equal space, remove mb-4 on medium screens */}
                                                        <div className="flex items-center gap-3 mb-2"> {/* Wrap header and select-all checkbox */}
                                                            <h3 className="text-lg font-semibold text-sky-700">DECK</h3>
                                                            {/* --- NEW: Select All Checkbox for DECK Ranks --- */}
                                                            <input
                                                                type="checkbox"
                                                                id="select-all-deck-ranks"
                                                                checked={seqRanks.length > 0 && seqRanks.every(r => selectedRankIds.has(r.id))}
                                                                ref={(input) => {
                                                                    if (input) {
                                                                        // Set indeterminate state if some but not all DECK ranks are selected
                                                                        input.indeterminate = seqRanks.length > 0 && selectedRankIds.size > 0 && !seqRanks.every(r => selectedRankIds.has(r.id)) && seqRanks.some(r => selectedRankIds.has(r.id));
                                                                    }
                                                                }}
                                                                onChange={() => handleSelectAllDeckRanksChange()} // Call the new handler
                                                                className="ml-4 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                                                            />
                                                            <label htmlFor="select-all-deck-ranks" className="ml-1 block text-xs font-medium text-gray-600">
                                                                Select All
                                                            </label>
                                                            {/* --- END NEW: Select All Checkbox for DECK Ranks --- */}
                                                        </div>
                                                        <div className="space-y-2 max-h-60 overflow-y-auto pr-4 scrollbar-gutter-stable">

                                                            {seqRanks.map((rank) => (
                                                                <div key={rank.id} className="grid grid-cols-[20px_1fr] items-center gap-3">

                                                                    <input
                                                                        type="checkbox"
                                                                        id={`deck-rank-${rank.id}`} // Unique ID for deck ranks
                                                                        checked={selectedRankIds.has(rank.id)}
                                                                        onChange={() => handleRankCheckboxChange(rank.id)}
                                                                        className="h-4 w-4 shrink-0 text-indigo-600 border-gray-300 rounded"

                                                                    />
                                                                    <label htmlFor={`deck-rank-${rank.id}`} className="text-sm text-gray-700 leading-tight">
                                                                        {rank.rank_name || rank.name || rank.rank_id || 'Unknown Rank'} {/* Adjust field names based on your rank object structure */}
                                                                    </label>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* ENGINE Ranks Section */}
                                                {technicalRanks.length > 0 && (
                                                    <div className="flex-1"> {/* Use flex-1 to take up equal space */}
                                                        <div className="flex items-center mb-2"> {/* Wrap header and select-all checkbox */}
                                                            <h3 className="text-lg font-semibold text-sky-700">ENGINE</h3>
                                                            {/* --- NEW: Select All Checkbox for ENGINE Ranks --- */}
                                                            <input
                                                                type="checkbox"
                                                                id="select-all-engine-ranks"
                                                                checked={technicalRanks.length > 0 && technicalRanks.every(r => selectedRankIds.has(r.id))}
                                                                ref={(input) => {
                                                                    if (input) {
                                                                        // Set indeterminate state if some but not all ENGINE ranks are selected
                                                                        input.indeterminate = technicalRanks.length > 0 && selectedRankIds.size > 0 && !technicalRanks.every(r => selectedRankIds.has(r.id)) && technicalRanks.some(r => selectedRankIds.has(r.id));
                                                                    }
                                                                }}
                                                                onChange={() => handleSelectAllEngineRanksChange()} // Call the new handler
                                                                className="ml-4 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                                                            />
                                                            <label htmlFor="select-all-engine-ranks" className="ml-1 block text-xs font-medium text-gray-600">
                                                                Select All
                                                            </label>
                                                            {/* --- END NEW: Select All Checkbox for ENGINE Ranks --- */}
                                                        </div>
                                                        <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                                                            {technicalRanks.map((rank) => (
                                                                <div key={rank.id} className="grid grid-cols-[20px_1fr] items-center gap-3">

                                                                    <input
                                                                        type="checkbox"
                                                                        id={`engine-rank-${rank.id}`} // Unique ID for engine ranks
                                                                        checked={selectedRankIds.has(rank.id)}
                                                                        onChange={() => handleRankCheckboxChange(rank.id)}
                                                                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                                                                    />
                                                                    <label htmlFor={`engine-rank-${rank.id}`} className="ml-3 block text-sm text-gray-700">
                                                                        {rank.rank_name || rank.name || rank.rank_id || 'Unknown Rank'} {/* Adjust field names based on your rank object structure */}
                                                                    </label>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Show message if no ranks loaded at all */}
                                                {allRanks.length === 0 && !loadingRanks && (
                                                    <div className="text-center py-4">
                                                        <p className="text-gray-500">No ranks found.</p>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                        {/* --- END NEW: Horizontal Layout --- */}

                                        {/* --- END NEW: Render Ranks in Groups --- */}


                                        {/* Action Buttons */}
                                        <div className="flex justify-end space-x-3 mt-6">
                                            <button
                                                type="button"
                                                onClick={handleCancelRankSelection}
                                                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg text-sm font-medium hover:bg-gray-300 transition"
                                            >
                                                Cancel
                                            </button>
                                            <button
                                                type="button"
                                                onClick={handleConfirmRankSelection}
                                                disabled={selectedRankIds.size === 0} // Disable if no ranks selected
                                                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${selectedRankIds.size === 0
                                                    ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                                                    : 'bg-sky-700 hover:bg-sky-800 text-white'
                                                    }`}
                                            >
                                                Confirm
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                        {/* --- END NEW: Rank Selection Popup Modal --- */}


                        {/* Action Buttons */}
                        <div className="flex justify-end gap-2 pt-4">
                            <WithPermission formId="PSC_F_009" processId="PSC_P_017">
                                <button
                                    type="button"
                                    onClick={handleSaveDraft}
                                    className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg text-sm font-medium hover:bg-gray-300 transition border border-gray-300"
                                >
                                    Save Draft
                                </button>
                            </WithPermission>
                            <WithPermission formId="PSC_F_009" processId="PSC_P_024">
                                <button
                                    type="button" // Changed from 'submit' to 'button'
                                    onClick={handleVesselSelectionForPublishing} // Call the new handler
                                    process-id="PSC_P_024"
                                    className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-sky-700 hover:bg-sky-800 text-white h-9 px-3"
                                >
                                    Publish
                                </button>
                            </WithPermission>
                            <WithPermission formId="PSC_F_009" processId="PSC_P_018">
                                <button
                                    type="button"
                                    onClick={handleSubmit}
                                    process-id="PSC_P_018"
                                    className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-sky-700 hover:bg-sky-800 text-white h-9 px-3"
                                >
                                    Submit for Approval
                                </button>
                            </WithPermission>

                            {/* --- NEW: Show Pending Requests Button --- */}
                            <WithPermission formId="PSC_F_009" processId="PSC_P_019">
                                <Button
                                    type="button"
                                    variant="outline"
                                    process-id="PSC_P_019"
                                    className="border-sky-200"
                                    onClick={() => {
                                        setShowPendingRequests(true); // Set state to show table
                                        // Scroll to the pending requests section after a brief delay
                                        setTimeout(() => {
                                            const pendingRequestsElement = document.getElementById('pending-requests-section');
                                            if (pendingRequestsElement) {
                                                pendingRequestsElement.scrollIntoView({
                                                    behavior: 'smooth',
                                                    block: 'start'
                                                });
                                            }
                                        }, 100);
                                    }}
                                >
                                    Show Pending Requests
                                </Button>
                            </WithPermission>
                        </div>
                    </form>
                </CardContent>
            </Card>


            {/* --- Conditionally Render Submitted Requests Table --- */}
            {showPendingRequests && submittedRequests.length > 0 && (
                <Card id="pending-requests-section" className="shadow-none border border-sky-100 rounded-xl bg-sky-50 text-sky-700 mt-6"> {/* Added mt-6 for spacing */}
                    <CardHeader className="pb-2 flex justify-between items-center">
                        <CardTitle className="text-lg font-semibold"> Approval Requests</CardTitle>
                        {/* --- NEW: Close Button --- */}
                        <Button
                            variant="outline"
                            size="sm"
                            className="border-sky-200"
                            onClick={() => setShowPendingRequests(false)} // Set state to hide table
                        >
                            Close
                        </Button>
                        {/* --- END NEW --- */}
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="text-xs font-medium">ID</TableHead>
                                    <TableHead className="text-xs font-medium">Type</TableHead>
                                    <TableHead className="text-xs font-medium">Priority</TableHead>
                                    <TableHead className="text-xs font-medium">Submitted at</TableHead>
                                    <TableHead className="text-xs font-medium">Status</TableHead>
                                    <TableHead className="text-right text-xs font-medium">View</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {submittedRequests.map((req) => (
                                    <TableRow key={req.id} className="hover:bg-sky-50/40">
                                        <TableCell className="text-xs font-medium">{req.id}</TableCell>

                                        <TableCell>{renderTypeBadge(req.type)}</TableCell>
                                        <TableCell>{renderPriorityBadge(req.priority)}</TableCell>
                                        <TableCell className="text-xs text-slate-600">{req.submitted}</TableCell>
                                        <TableCell>{renderStatusBadge(req.status)}</TableCell>
                                        <TableCell className="text-right">
                                            <div className="flex justify-end gap-2">
                                                <button
                                                    className="p-1.5 rounded-md hover:bg-sky-50 transition-colors"
                                                    onClick={() => setViewingRequest(req)}
                                                    aria-label="View request details"
                                                >
                                                    <svg
                                                        xmlns="http://www.w3.org/2000/svg"
                                                        width="16"
                                                        height="16"
                                                        viewBox="0 0 24 24"
                                                        fill="none"
                                                        stroke="currentColor"
                                                        strokeWidth="2"
                                                        strokeLinecap="round"
                                                        strokeLinejoin="round"
                                                        className="text-sky-600"
                                                    >
                                                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                                        <circle cx="12" cy="12" r="3" />
                                                    </svg>
                                                </button>


                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}

            {/* --- View Modal (Keep your existing one) --- */}
            {viewingRequest && (
                <WithPermission id="PSC_F_010">
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 " form-id="PSC_F_010">
                        <div className="bg-sky-50 text-sky-700 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-lg font-semibold">Request Details: {viewingRequest.title}</h2>
                                <button onClick={() => setViewingRequest(null)} className="text-gray-500 hover:text-gray-700">&times;</button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div><strong>ID:</strong> {viewingRequest.id}</div>
                                <div><strong>Type:</strong> {viewingRequest.type === 'alert' ? 'Alert' : viewingRequest.type === 'circular' ? 'Circular' : 'Work Instruction'}</div>
                                <div><strong>Priority:</strong> {viewingRequest.priority}</div>
                                <div><strong>created at:</strong> {viewingRequest.submitted}</div>
                                <div><strong>Status:</strong> {viewingRequest.status}</div>
                                <div><strong>Department:</strong> {viewingRequest.details.mainOption === 'seq' ? 'Seq' : 'Technical'}</div>
                                <div><strong>Category:</strong> {viewingRequest.details.category}</div>
                                <div><strong>Created By:</strong> {viewingRequest.created_by}</div>

                            </div>

                            {viewingRequest.details.sub1.length > 0 && (
                                <div className="mb-3">
                                    <strong>Flag / Class / P&I / Maker:</strong><br />
                                    {viewingRequest.details.sub1.join(', ')}
                                </div>
                            )}

                            <div className="mb-3">
                                <strong>
                                    {viewingRequest.details.mainOption === 'seq'
                                        ? 'Safety / Health / Cargo / Navigation / Operation / Documentation:'
                                        : 'Machinery / Bunker / Electrical / Lifting Appliance:'}
                                </strong><br />
                                {viewingRequest.details.sub2.join(', ')}
                            </div>

                            <div className="mb-3">
                                <strong>Body / Instructions:</strong><br />
                                <div className="bg-sky-50 p-3 rounded-md mt-1 border border-sky-200 whitespace-pre-wrap">
                                    {viewingRequest.details.body || 'â€”'}
                                </div>
                            </div>

                            {/* // --- Inside the modal JSX (e.g., within the div that shows when viewingRequest is set) --- */}
                            <div>
                                <strong>Attachments:</strong><br />
                                {/* --- CORRECTED: Safely access attachment_url and construct the full URL --- */}
                                {/* Check if viewingRequest and viewingRequest.attachment_url exist and are not empty strings */}
                                {viewingRequest && viewingRequest.attachment_url ? (
                                    <div className="mt-2">
                                        {/* Construct the full URL using the backend host and the path from the API response */}
                                        {/* Ensure the URL starts with  (or your actual backend URL) */}
                                        <a
                                            href={/^https?:\/\//i.test(viewingRequest.attachment_url) ? viewingRequest.attachment_url : "http://localhost:8000" + viewingRequest.attachment_url} //Correctly prepend the base URL
                                            target="_blank" // Opens the PDF in a new tab
                                            rel="noopener noreferrer" // Security best practice for target="_blank"
                                            className="inline-flex items-center px-3 py-1 border border-sky-300 text-sm font-medium rounded-md text-sky-700 bg-white hover:bg-sky-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 transition-colors duration-200"
                                        >
                                            {/* Optional: Add a PDF icon */}
                                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-file-earmark-pdf mr-1" viewBox="0 0 16 16">
                                                <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2M9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5z" />
                                                <path d="M4.603 14.087a.8.8 0 0 1-.438-.42c-.195-.388-.13-.776.08-1.102.198-.307.526-.568.897-.787a7.7 7.7 0 0 1 1.482-.645 20 20 0 0 0 1.062-2.227 7.3 7.3 0 0 1-.43-1.295c-.086-.4-.119-.796-.046-1.136.075-.354.274-.672.65-.823.192-.077.4-.12.602-.077a.7.7 0 0 1 .477.365c.088.164.12.356.127.538.007.188-.012.396-.047.614-.084.51-.27 1.134-.52 1.794a11 11 0 0 0 .98 1.686 5.8 5.8 0 0 1 1.334.05c.364.066.734.195.96.465.12.144.193.32.2.518.007.192-.047.382-.138.563a1.04 1.04 0 0 1-.354.416.86.86 0 0 1-.51.138c-.331-.014-.654-.196-.933-.417a5.7 5.7 0 0 1-.911-.95 11.7 11.7 0 0 0-1.997.406 11.3 11.3 0 0 1-1.02 1.51c-.292.35-.609.656-.927.787a.8.8 0 0 1-.58.029m1.379-1.901q-.25.115-.459.238c-.328.194-.541.383-.647.547-.094.145-.096.25-.04.361q.016.032.026.044l.035-.012c.137-.056.355-.235.635-.572a8 8 0 0 0 .45-.606m1.64-1.33a13 13 0 0 1 1.01-.193 12 12 0 0 1-.51-.858 21 21 0 0 1-.5 1.05zm2.446.45q.226.245.435.41c.24.19.407.253.498.256a.1.1 0 0 0 .07-.015.3.3 0 0 0 .094-.125.44.44 0 0 0 .059-.2.1.1 0 0 0-.026-.063c-.052-.062-.2-.152-.518-.209a4 4 0 0 0-.612-.053zM8.078 7.8a7 7 0 0 0 .2-.828q.046-.282.038-.465a.6.6 0 0 0-.032-.198.5.5 0 0 0-.145.04c-.087.035-.158.106-.196.283-.04.192-.03.469.046.822q.036.167.09.346z" />
                                            </svg>
                                            Open PDF
                                        </a>
                                    </div>
                                ) : (
                                    // If viewingRequest is null/undefined or viewingRequest.attachment_url is null/undefined/empty string
                                    <span className="text-gray-500 italic">No files attached</span>
                                )}
                                {/* --- END CORRECTED --- */}
                            </div>

                            <div className="text-right mt-6">
                                <Button onClick={() => setViewingRequest(null)} className="bg-sky-700 hover:bg-sky-800 text-white">
                                    Close
                                </Button>
                            </div>
                        </div>
                    </div>
                </WithPermission>
            )}
            {/* --- End View Modal --- */}



            {/* Pending Requests Table */}
            {submittedRequests.length > 0 && (
                <WithPermission id="PSC_F_011">
                    <Card className="shadow-none border border-sky-100 rounded-xl bg-sky-50 text-sky-700" form-id="PSC_F_011">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-lg font-semibold">Pending Approval Requests</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="text-xs font-medium">ID</TableHead>
                                        <TableHead className="text-xs font-medium">Type</TableHead>
                                        <TableHead className="text-xs font-medium">Priority</TableHead>
                                        <TableHead className="text-xs font-medium">Submitted</TableHead>
                                        <TableHead className="text-xs font-medium">Status</TableHead>
                                        <TableHead className="text-right text-xs font-medium">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {submittedRequests.map((req) => (
                                        <TableRow key={req.id} className="hover:bg-sky-50/40">
                                            <TableCell className="text-xs font-medium">{req.sr_no}</TableCell>
                                            <TableCell>{renderTypeBadge(req.type)}</TableCell>
                                            <TableCell>{renderPriorityBadge(req.priority)}</TableCell>
                                            <TableCell className="text-xs text-slate-600">{req.submitted}</TableCell>
                                            <TableCell>{renderStatusBadge(req.status)}</TableCell>
                                            <TableCell className="text-right">
                                                <div className="flex justify-end gap-2">
                                                    <WithPermission formId="PSC_F_011" processId="PSC_P_025">
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            className="border-sky-200"
                                                            process-id="PSC_P_025"
                                                            onClick={() => setViewingRequest(req)}
                                                        >
                                                            View
                                                        </Button>
                                                    </WithPermission>
                                                    {/* Edit Button (for Pending notifications) */}
                                                    {/* Only show Edit button if publish_status is 1 (Pending) */}

                                                    {/* <Button
                                                                               onClick={() => handleEditPendingNotification(req.sr_no)} // Pass the SR No for editing
                                                                               size="sm"
                                                                               className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md shadow-sm text-blue-800 bg-blue-200 hover:bg-blue-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-400"
                                                                               aria-label={`Edit ${req.sr_no}`}
                                                                               title={`Edit ${req.sr_no}`}
                                                                           >
                                                                               Edit
                                                                           </Button> */}



                                                    <WithPermission formId="PSC_F_011" processId="PSC_P_026">
                                                        <Button
                                                            size="sm"
                                                            className="bg-emerald-200 hover:bg-emerald-300 text-emerald-800"
                                                            onClick={() => handleApproveReject(req.sr_no, 'approve')}
                                                            process-id="PSC_P_026"
                                                        >
                                                            Approve
                                                        </Button>
                                                    </WithPermission>
                                                    <WithPermission formId="PSC_F_011" processId="PSC_P_027">
                                                        <Button
                                                            size="sm"
                                                            className="bg-rose-200 hover:bg-rose-300 text-rose-800"
                                                            onClick={() => handleApproveReject(req.sr_no, 'reject')}
                                                            process-id="PSC_P_027"
                                                        >
                                                            Reject
                                                        </Button>
                                                    </WithPermission>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </WithPermission>
            )}


            {/* View Modal */}
            {viewingRequest && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 ">
                    <div className="bg-sky-50 text-sky-700 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-semibold">Request Details: {viewingRequest.sr_no}</h2>
                            <button onClick={() => setViewingRequest(null)} className="text-gray-500 hover:text-gray-700">&times;</button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                            <div><strong>ID:</strong> {viewingRequest.sr_no}</div>
                            <div><strong>Type:</strong> {viewingRequest.type === 'alert' ? 'Alert' : viewingRequest.type === 'circular' ? 'Circular' : 'Work Instruction'}</div>
                            <div><strong>Priority:</strong> {viewingRequest.priority}</div>
                            <div><strong>Submitted:</strong> {viewingRequest.submitted}</div>
                            <div><strong>Status:</strong> {viewingRequest.status}</div>
                            <div><strong>Department:</strong> {viewingRequest.details.mainOption === 'seq' ? 'Seq' : 'Technical'}</div>
                            <div><strong>Category:</strong> {viewingRequest.details.category}</div>
                            <div><strong>Created By:</strong> {viewingRequest.created_by}</div>
                        </div>

                        {viewingRequest.details.sub1.length > 0 && (
                            <div className="mb-3">
                                <strong>Flag / Class / P&I / Maker:</strong><br />
                                {viewingRequest.details.sub1.join(', ')}
                            </div>
                        )}

                        <div className="mb-3">
                            <strong>
                                {viewingRequest.details.mainOption === 'seq'
                                    ? 'Safety / Health / Cargo / Navigation / Operation / Documentation:'
                                    : 'Machinery / Bunker / Electrical / Lifting Appliance:'}
                            </strong><br />
                            {viewingRequest.details.sub2.join(', ')}
                        </div>

                        <div className="mb-3">
                            <strong>Body / Instructions:</strong><br />
                            <div className="bg-sky-50 p-3 rounded-md mt-1 border border-sky-200 whitespace-pre-wrap">
                                {viewingRequest.details.body || 'â€”'}
                            </div>
                        </div>

                        {/* Attachments Section - Updated */}
                        <div>
                            <strong>Attachments:</strong><br />
                            {viewingRequest.attachment_url ? (
                                <div className="mt-2">

                                    <a
                                        href={/^https?:\/\//i.test(viewingRequest.attachment_url) ? viewingRequest.attachment_url : "http://localhost:8000" + viewingRequest.attachment_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center px-3 py-2 border border-sky-300 text-sm font-medium rounded-md text-sky-700 bg-white hover:bg-sky-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 transition-colors duration-200"
                                    >

                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-earmark-pdf" viewBox="0 0 16 16">
                                            <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2M9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5z" />
                                            <path d="M4.603 14.087a.8.8 0 0 1-.438-.42c-.195-.388-.13-.776.08-1.102.198-.307.526-.568.897-.787a7.7 7.7 0 0 1 1.482-.645 20 20 0 0 0 1.062-2.227 7.3 7.3 0 0 1-.43-1.295c-.086-.4-.119-.796-.046-1.136.075-.354.274-.672.65-.823.192-.077.4-.12.602-.077a.7.7 0 0 1 .477.365c.088.164.12.356.127.538.007.188-.012.396-.047.614-.084.51-.27 1.134-.52 1.794a11 11 0 0 0 .98 1.686 5.8 5.8 0 0 1 1.334.05c.364.066.734.195.96.465.12.144.193.32.2.518.007.192-.047.382-.138.563a1.04 1.04 0 0 1-.354.416.86.86 0 0 1-.51.138c-.331-.014-.654-.196-.933-.417a5.7 5.7 0 0 1-.911-.95 11.7 11.7 0 0 0-1.997.406 11.3 11.3 0 0 1-1.02 1.51c-.292.35-.609.656-.927.787a.8.8 0 0 1-.58.029m1.379-1.901q-.25.115-.459.238c-.328.194-.541.383-.647.547-.094.145-.096.25-.04.361q.016.032.026.044l.035-.012c.137-.056.355-.235.635-.572a8 8 0 0 0 .45-.606m1.64-1.33a13 13 0 0 1 1.01-.193 12 12 0 0 1-.51-.858 21 21 0 0 1-.5 1.05zm2.446.45q.226.245.435.41c.24.19.407.253.498.256a.1.1 0 0 0 .07-.015.3.3 0 0 0 .094-.125.44.44 0 0 0 .059-.2.1.1 0 0 0-.026-.063c-.052-.062-.2-.152-.518-.209a4 4 0 0 0-.612-.053zM8.078 7.8a7 7 0 0 0 .2-.828q.046-.282.038-.465a.6.6 0 0 0-.032-.198.5.5 0 0 0-.145.04c-.087.035-.158.106-.196.283-.04.192-.03.469.046.822q.036.167.09.346z" />
                                        </svg>
                                        Open PDF
                                    </a>
                                </div>
                            ) : (
                                <span className="text-gray-500 italic">No files attached</span>
                            )}
                        </div>

                        <div className="text-right mt-6">
                            <Button onClick={() => setViewingRequest(null)} className="bg-sky-700 hover:bg-sky-800 text-white">
                                Close
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>

    );
};

export default Admin;
