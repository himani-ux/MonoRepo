// src/components/MainDashboard.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AppHeader from '../../components/orb/AppHeader'; // Adjust path as needed
import AppFooter from '../../components/orb/AppFooter'; // Adjust path as needed
import CrewDashboard from '../../components/orb/crew/CrewDashboard'; // Adjust path as needed
import ChiefDashboard from '../../components/orb/files/ChiefDashboard'; // Adjust path as needed
import { useAuth } from '../../hooks/auth/useAuth';

export default function MainDashboard() {
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const {user} = useAuth();
  // console.log("MainDashboard: Current user data from useAuth:", user);

  useEffect(() => {
    
    
    if (!user) {
      // If no user data is found, redirect to login
      console.error("MainDashboard: No user found in sessionStorage. Redirecting to login.");
      navigate('/login');
      return;
    }

    try {
      
      // Determine role based on the is_chief flag received during login
      // Adjust the key name if your login system uses a different key to determine chief status
      const isChief = user?.is_chief; // This flag should be set during login based on rank
      // console.log(`MainDashboard: User is chief: ${isChief}`);

      if (isChief === true) {
        setUserRole('chief');
      } else if (isChief === false) {
        setUserRole('crew');
      } else {
        // If is_chief is undefined or not a boolean, try to determine from rank name as fallback
        const rankName = user?.rank?.toUpperCase();
        console.log(`MainDashboard: User rank is '${rankName}'`);
        const chiefRanks = ["MASTER", "CHIEF ENGINEER", "CHIEF OFFICER"]; // Adjust as needed
        if (chiefRanks.includes(rankName)) {
          setUserRole('chief');
        } else {
          setUserRole('crew');
        }
      }
      console.log("MainDashboard: Determined user role:", userRole);
    } catch (error) {
      console.error("MainDashboard: Error parsing user data from sessionStorage:", error);
      navigate('/login'); // Redirect on error
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  if (loading) {
    return (
      <div className="orb-theme">
     
        <main style={{ padding: '20px', textAlign: 'center' }}>
          <p>Loading dashboard...</p>
        </main>

      </div>
    );
  }

  return (
    <div className="orb-theme">
    
      <main style={{ padding: '20px' }}>
        {/* Conditionally render the appropriate dashboard component */}
        {userRole === 'chief' ? <ChiefDashboard /> : <CrewDashboard />}
      </main>

    </div>
  );
}







// src/pages/orb/MainDashboard.jsx
// Unified dashboard router - automatically detects user role and renders appropriate view

// import React from 'react';
// import { useNavigate } from 'react-router-dom';
// import UnifiedDashboard from '../../components/orb/crew/Dashboard';
// import { useAuth } from '../../hooks/auth/useAuth';

// export default function MainDashboard() {
//   const navigate = useNavigate();
//   const { user } = useAuth();

//   React.useEffect(() => {
//     if (!user) {
//       console.error('MainDashboard: No user found. Redirecting to login.');
//       navigate('/login');
//     }
//   }, [user, navigate]);

//   if (!user) {
//     return (
//       <div className="orb-theme">
//         <main style={{ padding: '20px', textAlign: 'center' }}>
//           <p>Loading dashboard...</p>
//         </main>
//       </div>
//     );
//   }

//   // UnifiedDashboard automatically detects role based on user.rank
//   return <UnifiedDashboard />;
// }