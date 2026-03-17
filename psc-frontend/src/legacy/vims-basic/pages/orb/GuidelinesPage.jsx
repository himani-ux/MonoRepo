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
   
    <div className="guidelines-page orb-theme" style={{ padding: '20px' }}>
      <Card title="Guidelines">
        <div className="p-card-content">
          <p>Please select the guideline document you wish to view or download:</p>
          <ul style={{ listStyleType: 'none', padding: 0 }}>
            <li style={{ marginBottom: '10px' }}>
              <a
                href={correctEntriesPdfPath}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  textDecoration: 'none',
                  color: '#030303ff',
                  padding: '10px 15px',
                  border: '1px solid #007bff',
                  borderRadius: '4px',
                  display: 'inline-block',
                  backgroundColor: '#f8f9fa',
                  fontWeight: '500',
                  fontSize: '14px'
                }}
              >
                ORB Correct Entries Guidelines
              </a>
            </li>
            <li style={{ marginBottom: '10px' }}>
              <a
                href={softwareGuidelinesPdfPath}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  textDecoration: 'none',
                  color: '#020202ff',
                  padding: '10px 15px',
                  border: '1px solid #007bff',
                  borderRadius: '4px',
                  display: 'inline-block',
                  backgroundColor: '#f8f9fa',
                  fontWeight: '500',
                  fontSize: '14px'
                }}
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
