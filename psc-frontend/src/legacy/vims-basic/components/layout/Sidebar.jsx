import { NavLink } from "react-router-dom";
import { getModulesByUserType } from "../../navigation/modules";
import { useSelector } from "react-redux";
import { useState } from "react";
import { useAuth } from "../../hooks/auth/useAuth";

const Sidebar = () => {
  const sidebarOpen = useSelector((state) => state.ui.sidebarOpen);
  const { user } = useAuth();
  const [openModule, setOpenModule] = useState(null);
  
  // Get modules based on user type
  const modules = getModulesByUserType(user?.user_type);

 

  const handleModuleClick = (module) => {
    // If module has no pages (pages array is empty), navigate to base path
    if (!module.pages || module.pages.length === 0) {
      // Close the dropdown and navigate directly
      setOpenModule(null);
      // Navigation will be handled by NavLink to basePath
      return;
    }
    // Otherwise, toggle the module dropdown
    setOpenModule(openModule === module.key ? null : module.key);
  };

  return (
    <aside className={`
    w-64 bg-gray-900 text-white p-4 overflow-y-auto
    transition-all duration-300 ease-in-out
    ${sidebarOpen ? "max-w-64 opacity-100" : "max-w-0 opacity-0"}
  `}>
      <h2 className="text-xl font-bold mb-6">Modules</h2>

      {modules.map((module) => {
        const hasPages = module.pages && module.pages.length > 0;

        // If no pages, render as a direct NavLink
        if (!hasPages) {
          return (
            <NavLink
              key={module.key}
              to={module.basePath}
              className={({ isActive }) =>
                `flex items-center px-3 py-2 rounded mb-2 ${
                  isActive ? "bg-gray-700" : "hover:bg-gray-700"
                }`
              }
            >
              <span>{module.icon} {module.label}</span>
            </NavLink>
          );
        }

        // If pages exist, render as collapsible dropdown
        return (
          <div key={module.key} className="mb-2">
            <button
              onClick={() =>
                setOpenModule(openModule === module.key ? null : module.key)
              }
              className="w-full flex justify-between items-center px-3 py-2 rounded hover:bg-gray-700"
            >
              <span>{module.icon} {module.label}</span>
              <span>{openModule === module.key ? "▾" : "▸"}</span>
            </button>

            {openModule === module.key && (
              <div className="ml-4 mt-1">
                {module.pages.map((page) => (
                  <NavLink
                    key={page.path}
                    to={page.path}
                    className={({ isActive }) =>
                      `block px-3 py-1 rounded text-sm ${
                        isActive ? "bg-gray-700" : "hover:bg-gray-800"
                      }`
                    }
                  >
                    {page.label}
                  </NavLink>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </aside>
  );
};

export default Sidebar;


