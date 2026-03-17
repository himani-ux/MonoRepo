// src/utils/permissionUtils.js

import { useAuth } from "../../hooks/auth/useAuth";

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


/**
 * Checks if the logged-in user has permission for a specific form or process.
 * Uses data stored in sessionStorage under 'currentUser'.
 *
 * @param {string} id - The form ID (e.g., "F_001") or process ID (e.g., "P_002").
 * @returns {boolean} - True if user has permission, false otherwise.
 */
export const hasPermission = (id) => {
    // Retrieve user data from sessionStorage
    const {user} = useAuth();
    
    if (!user) {
        // console.error("hasPermission: No user found in sessionStorage.");
        return false;
    }

    
    // try {
    //     console.log(`hasPermission: Checking permissions for user ${user.CrewID || user.UserId} on ID '${id}'`);
        
    // } catch (e) {
    //     console.error("hasPermission: Error parsing user data from sessionStorage:", e);
    //     return false;
    // }

    // Get the assigned_form_ids and assigned_process_ids from the user object
    // They might be arrays or strings depending on how they were stored
    let assignedFormIds = user.form_ids;
    let assignedProcessIds = user.process_ids;

    // If assignedFormIds is a string, try to parse it as JSON
    if (typeof assignedFormIds === 'string') {
        try {
            assignedFormIds = JSON.parse(assignedFormIds);
            // console.log(`hasPermission: Parsed assignedFormIds from string:`, assignedFormIds);
        } catch (parseError) {
            // console.warn(`hasPermission: Failed to parse assignedFormIds from string: ${parseError.message}. Using empty array.`);
            assignedFormIds = [];
        }
    }

    // If assignedProcessIds is a string, try to parse it as JSON
    if (typeof assignedProcessIds === 'string') {
        try {
            assignedProcessIds = JSON.parse(assignedProcessIds);
            // console.log(`hasPermission: Parsed assignedProcessIds from string:`, assignedProcessIds);
        } catch (parseError) {
            // console.warn(`hasPermission: Failed to parse assignedProcessIds from string: ${parseError.message}. Using empty array.`);
            assignedProcessIds = [];
        }
    }

    // Ensure they are arrays
    if (!Array.isArray(assignedFormIds)) {
        // console.warn(`hasPermission: assigned_form_ids is not an array for user ${user.CrewID || user.UserId}.`);
        assignedFormIds = [];
    }

    if (!Array.isArray(assignedProcessIds)) {
        // console.warn(`hasPermission: assigned_process_ids is not an array for user ${user.CrewID || user.UserId}.`);
        assignedProcessIds = [];
    }

    // Check if the ID starts with 'F_' (Form) or 'P_' (Process)
    if (id.startsWith('F_') || id.startsWith('PSC_F_')) {
        // console.log(`hasPermission: Checking form ID '${id}' against assigned_form_ids:`, assignedFormIds);

        // Return true if the ID is in the assignedFormIds array
        const normalizedAssignedFormIds = assignedFormIds.map((value) => normalizePermissionId(value, 'form'));
        return normalizedAssignedFormIds.includes(normalizePermissionId(id, 'form'));

    } else if (id.startsWith('P_') || id.startsWith('PSC_P_')) {
        // console.log(`hasPermission: Checking process ID '${id}' against assigned_process_ids:`, assignedProcessIds);

        // Return true if the ID is in the assignedProcessIds array
        const normalizedAssignedProcessIds = assignedProcessIds.map((value) => normalizePermissionId(value, 'process'));
        return normalizedAssignedProcessIds.includes(normalizePermissionId(id, 'process'));

    } else {
        // console.warn(`hasPermission: Unknown ID format '${id}'. Must start with 'F_', 'P_', 'PSC_F_' or 'PSC_P_'.`);
        return false;
    }
};

/**
 * Utility function to conditionally render content based on permission.
 * Use this to wrap any component or JSX that should be shown only if the user has permission.
 *
 * @param {string} id - The form ID or process ID.
 * @param {React.ReactNode} children - The content to render if permission is granted.
 * @param {React.ReactNode} [fallback=null] - Optional content to render if permission is denied.
 * @returns {React.ReactNode} - The children if permission is granted, fallback otherwise.
 */
export const WithPermission = ({ id, children, fallback = null }) => {
    if (hasPermission(id)) {
        return children;
    } else {
        return fallback;
    }
};
