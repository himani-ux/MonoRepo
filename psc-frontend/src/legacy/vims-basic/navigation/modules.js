/**
 * VIMS Modules Configuration
 * 
 * Each module represents a major section of the VIMS application.
 * For Circular: Navigation is form/process ID based (no static pages needed).
 * These IDs come from the backend and are stored in user.form_ids and user.process_ids
 */
const ALL_MODULES = [
    {
        key: "circular",
        label: "Circular",
        icon: "📋",
        basePath: "/circular",
        // No pages array - navigation based on form_ids and process_ids from backend
        pages: [],
        description: "Manage circulars with form-based and process-based permissions",
        visibleTo: ["ship", "office"] // Visible to both ship and office users
    },
    {
        key: "orb",
        label: "ORB",
        icon: "🚢",
        basePath: "/orb",
        // No pages array - ORB module structure TBD
        pages: [],
        description: "Online Reporting Bureau",
        visibleTo: ["ship"] // Only visible to ship users
    },
];

/**
 * Get modules filtered by user type
 * @param {string} userType - The user type ('ship' or 'office')
 * @returns {array} Array of modules visible to the user type
 */
export const getModulesByUserType = (userType) => {
    if (!userType) return [];
    return ALL_MODULES.filter(module => 
        module.visibleTo && module.visibleTo.includes(userType)
    );
};

// Default export for backward compatibility
export const MODULES = ALL_MODULES;
