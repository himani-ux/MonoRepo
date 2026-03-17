// //---------------------------------------VERSION 1.0---------------------------------------//


// import Header from "./Header";
// import Sidebar from "./Sidebar";
// import Footer from "./Footer";
// import Breadcrumbs from "./Breadcrumbs";

// // const PageLayout = ({ children }) => {
// //   return (
// //     <div className="flex h-screen overflow-hidden">
// //       <Sidebar />

// //       <div className="flex flex-col flex-1">
// //         <Header />
// //         <Breadcrumbs />

// //         <main className="flex-1 p-4 bg-gray-100 overflow-auto">
// //           {children}
// //         </main>

// //         <Footer />
// //       </div>
// //     </div>
// //   );
// // };

// // export default PageLayout;





// //---------------------------------------VERSION 2.0---------------------------------------//



import Footer from "./Footer";
import Breadcrumbs from "./Breadcrumbs";
import { useAuthStore } from "@/stores/auth-store";

const PageLayout = ({ 
  children, 
  userName,
  onLogout,
  customTitle,
  navbar,
  headerRightContent,
  footerContent,
  hideHeader = false,
  showBreadcrumbs = true
}) => {
  const handleLogout = async () => {
    await useAuthStore.getState().logout();
    if (onLogout) {
      onLogout();
    }
  };

  return (
    <div className="flex min-h-full flex-col gap-4">
      {!hideHeader && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-gradient-to-r from-sky-50 via-sky-100 to-slate-100 shadow-sm">
          <div className="flex min-h-14 items-center justify-between px-4">
            <div className="flex items-center gap-3">
              <div className="font-semibold text-lg">
                {customTitle || "VIMS"}
              </div>
            </div>

            <div className="flex items-center gap-4">
              {headerRightContent}
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

          {navbar && (
            <div className="flex justify-center border-t border-slate-200 py-2 px-4">
              {navbar}
            </div>
          )}
        </div>
      )}

      {showBreadcrumbs && <Breadcrumbs />}

      <main className="flex-1 overflow-auto">
        {children}
      </main>

      <Footer customContent={footerContent} />
    </div>
  );
};

export default PageLayout;


//---------------------------------------VERSION 3.0---------------------------------------//

// const PageLayout = ({ 
//   children, 
//   userName,
//   onLogout,
//   customTitle,
//   headerRightContent,
//   footerContent,
//   showBreadcrumbs = true
// }) => {
//   return (
//     <div className="flex h-screen"> {/* REMOVED overflow-hidden */}
//       <Sidebar />

//       <div className="flex flex-col flex-1 relative"> {/* ADDED relative */}
//         <Header 
//           userName={userName}
//           onLogout={onLogout}
//           customTitle={customTitle}
//           rightContent={headerRightContent}
//         />
//         {showBreadcrumbs && <Breadcrumbs />}

//         <main className="flex-1 p-4 bg-gray-100 overflow-y-auto">
//           {children}
//         </main>

//         <Footer customContent={footerContent} />
//       </div>
//     </div>
//   );
// };

// export default PageLayout;
