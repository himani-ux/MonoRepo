// components/PageNotFound.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function PageNotFound() {
  const navigate = useNavigate();
  return (
    <div style={{ textAlign: 'center', padding: '50px', fontFamily: 'Arial' }}>
      <h2>🚫 Page Not Found</h2>
      <p>This page does not exist.</p>
      <button onClick={() => navigate('/')} className="btn-primary">
        Back to Start
      </button>
    </div>
  );
}