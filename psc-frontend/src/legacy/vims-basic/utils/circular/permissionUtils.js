// src/utils/permissionUtils.js

import { useAuthStore } from "@/stores/auth-store";

/**
 * Converts a string or array to an array of IDs.
 * Handles both JSON array format and comma-separated format.
 * 
 * @param {string|array} data - The data to convert (JSON string, comma-separated string, or array)
 * @returns {array} - Array of IDs, or empty array if parsing fails
 */
const parseIdsData = (data) => {
    if (!data) return [];
    
    // If already an array, return as is
    if (Array.isArray(data)) {
        return data;
    }
    
    // If it's a string, try different parsing methods
    if (typeof data === 'string') {
        // Try JSON parsing first
        try {
            const parsed = JSON.parse(data);
            if (Array.isArray(parsed)) {
                return parsed;
            }
        } catch (e) {
            // JSON parsing failed, try comma-separated
        }
        
        // Try comma-separated parsing
        try {
            const ids = data.split(',').map(id => id.trim()).filter(id => id.length > 0);
            return ids;
        } catch (e) {
            console.error("parseIdsData: Failed to parse IDs:", e);
            return [];
        }
    }
    
    return [];
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

/**
 * Checks if the logged-in user has permission for a specific form or process.
 * Uses data stored in Redux state (via useAuth hook preferred, or localStorage as fallback).
 *
 * @param {string} id - The form ID (e.g., "F_001") or process ID (e.g., "P_002").
 * @returns {boolean} - True if user has permission, false otherwise.
 */
export const hasPermission = (id) => {
    const user = useAuthStore.getState().user;
    if (!user) {
        console.error("hasPermission: No authenticated user found.");
        return false;
    }

    // Get the form_ids and process_ids from the user object
    const formIdsData = user.form_ids;
    const processIdsData = user.process_ids;

    // Check if the ID starts with 'F_' (Form) or 'P_' (Process)
    if (id.startsWith('F_') || id.startsWith('PSC_F_')) {
        if (!formIdsData) {
            console.warn(`hasPermission: No form_ids found for user ${user.username}.`);
            return false;
        }

        try {
            const formIdsArray = parseIdsData(formIdsData);
            console.log(`hasPermission: Checking form ID '${id}' against form_ids:`, formIdsArray);

            // Return true if the ID is in the array
            const normalizedFormIds = Array.isArray(formIdsArray)
                ? formIdsArray.map((value) => normalizePermissionId(value, 'form'))
                : [];
            return normalizedFormIds.includes(normalizePermissionId(id, 'form'));
        } catch (e) {
            console.error(`hasPermission: Error processing form_ids for user ${user.username}:`, e);
            return false;
        }
    } else if (id.startsWith('P_') || id.startsWith('PSC_P_')) {
        if (!processIdsData) {
            console.warn(`hasPermission: No process_ids found for user ${user.username}.`);
            return false;
        }

        try {
            const processIdsArray = parseIdsData(processIdsData);
            console.log(`hasPermission: Checking process ID '${id}' against process_ids:`, processIdsArray);

            // Return true if the ID is in the array
            const normalizedProcessIds = Array.isArray(processIdsArray)
                ? processIdsArray.map((value) => normalizePermissionId(value, 'process'))
                : [];
            return normalizedProcessIds.includes(normalizePermissionId(id, 'process'));
        } catch (e) {
            console.error(`hasPermission: Error processing process_ids for user ${user.username}:`, e);
            return false;
        }
    } else {
        console.warn(`hasPermission: Unknown ID format '${id}'. Must start with 'F_', 'P_', 'PSC_F_' or 'PSC_P_'.`);
        return false;
    }
};

/**
 * Checks whether a user has both the required form and process permissions.
 *
 * @param {string} formId - The form ID (e.g. "F_001")
 * @param {string} processId - The process ID (e.g. "P_008")
 * @returns {boolean} - True when both permissions are present.
 */
export const hasPermissionPair = (formId, processId) => {
    if (!formId || !processId) {
        return false;
    }

    return hasPermission(formId) && hasPermission(processId);
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
export const WithPermission = ({ id, formId, processId, children, fallback = null }) => {
    const isAllowed = formId && processId
        ? hasPermissionPair(formId, processId)
        : hasPermission(id);

    if (isAllowed) {
        return children;
    } else {
        return fallback;
    }
};
