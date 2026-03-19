// src/components/GuidelinesPage.jsx
import React from 'react';
import { Card } from '../../components/orb/OrbUI'; 
import '../../styles/orb/GuidelinesPage.css'; 
import { useAuth } from '../../hooks/auth/useAuth';
import PageLayout from '../../components/layout/PageLayout'; // Import the PageLayout component


const GuidelinesPage = () => {
  const correctEntriesPdfPath = "/guidelines/ORB-PART-I-CORRECT-ENTRIES-ed.2021.pdf";
  const softwareGuidelinesPdfPath = "/guidelines/E-ORB GUIDELINES (1).pdf"; 
  const { user } = useAuth(); // Get user info from auth context

  return (
    <div className="guidelines-page orb-theme">
      <Card title="Guidelines">
        <div className="p-card-content">
          <p>Please select the guideline document you wish to view or download:</p>
          <ul className="orb-link-list">
            <li>
              <a
                href={correctEntriesPdfPath}
                target="_blank"
                rel="noopener noreferrer"
                className="orb-link-card"
              >
                ORB Correct Entries Guidelines
              </a>
            </li>
            <li>
              <a
                href={softwareGuidelinesPdfPath}
                target="_blank"
                rel="noopener noreferrer"
                className="orb-link-card"
              >
                Software Guidelines        
                
              </a>
            </li>
          </ul>
        </div>
      </Card>
    </div>
   
  );
};

export default GuidelinesPage;
