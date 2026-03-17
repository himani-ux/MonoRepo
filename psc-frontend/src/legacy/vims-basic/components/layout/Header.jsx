
// import { useDispatch } from "react-redux";
// import { toggleSidebar } from "../../store/uiSlice";
// import { logout } from "../../services/auth/authSlice";
// import { authApi } from "../../services/auth/authApi";
// import { useNavigate } from "react-router-dom";

// const Header = ({ 
//   userName, 
//   onLogout, 
//   customTitle, 
//   navbar,
//   rightContent 
// }) => {
//   const dispatch = useDispatch();
//   const navigate = useNavigate();

//   const handleLogout = () => {
//     if (onLogout) {
//       onLogout();
//     } else {
//       dispatch(logout());
//       dispatch(authApi.util.resetApiState());
//     }
//   };

//   return (
//     <header className="h-14 bg-gradient-to-r from-sky-50 via-sky-100 to-slate-100 border-b border-slate-200 flex items-center justify-between px-4 shadow-sm">
//       {/* Left */}
//       <div className="flex items-center gap-3">
//         <button
//           onClick={() => dispatch(toggleSidebar())}
//           className="p-2 rounded hover:bg-gray-100 cursor-pointer"
//         >
//           ☰
//         </button>
//         <h1 className="font-semibold text-lg">
//           {customTitle || "VIMS"}
//         </h1>
//       </div>

//       {/* Right */}
//       <div className="flex items-center gap-4">
//         {navbar || rightContent || (
//           <>
//             <span className="text-sm text-gray-600">
//               Welcome{userName ? `, ${userName}` : ""}!
//             </span>
//             <button
//               onClick={handleLogout}
//               className="px-3 py-1 text-sm bg-red-600 text-white rounded font-medium hover:bg-red-700 transition"
//             >
//               Logout
//             </button>
//           </>
//         )}
//       </div>
//     </header>
//   );
// };

// export default Header;


import { useDispatch } from "react-redux";
import { toggleSidebar } from "../../store/uiSlice";
import { logout } from "../../services/auth/authSlice";
import { authApi } from "../../services/auth/authApi";
import { useNavigate } from "react-router-dom";

const Header = ({ 
  userName, 
  onLogout, 
  customTitle, 
  navbar,
  rightContent 
}) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
    } else {
      dispatch(logout());
      dispatch(authApi.util.resetApiState());
    }
  };

  return (
    <header className="bg-gradient-to-r from-sky-50 via-sky-100 to-slate-100 border-b border-slate-200 shadow-sm">
      
      {/* ===== TOP ROW ===== */}
      <div className="h-14 flex items-center justify-between px-4">
        
        {/* Left : Sidebar + Title */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => dispatch(toggleSidebar())}
            className="p-2 rounded hover:bg-gray-100 cursor-pointer"
          >
            ☰
          </button>

          <h1 className="font-semibold text-lg">
            {customTitle || "VIMS"}
          </h1>
        </div>

        {/* Right : Welcome + Logout ALWAYS visible */}
        <div className="flex items-center gap-4">
          {rightContent}

          <span className="text-sm text-gray-600">
            Welcome{userName ? `, ${userName}` : ""}!
          </span>

          <button
            onClick={handleLogout}
            className="px-3 py-1 text-sm bg-red-600 text-white rounded font-medium hover:bg-red-700 transition"
          >
            Logout
          </button>
        </div>
      </div>

      {/* ===== NAVBAR ROW (CENTERED) ===== */}
      {navbar && (
        <div className="flex justify-center border-t border-slate-200 py-2">
          {navbar}
        </div>
      )}

    </header>
  );
};

export default Header;

