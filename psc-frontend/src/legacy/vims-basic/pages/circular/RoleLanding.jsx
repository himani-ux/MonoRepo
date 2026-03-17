// src/components/RoleLanding.jsx
import React, { useEffect } from 'react';
import { HiLibrary } from "react-icons/hi";
import { useNavigate } from 'react-router-dom';
import { useAuth } from "../../hooks/auth/useAuth";

export default function RoleLanding() {
  const navigate = useNavigate();
  const {user} = useAuth();
  useEffect(() => {
    if (!user) {
      navigate('/login');
    } else {
      // Optional: fetch initial data here
      // Then go to dashboard
      navigate('/dashboard', { replace: true });
    }
  }, [navigate, user]);

  return <div>Loading...</div>;
}