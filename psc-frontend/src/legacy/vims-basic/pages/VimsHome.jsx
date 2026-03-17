
import { useState, useEffect, use } from 'react';
import { useNavigate } from 'react-router-dom';
import PageLayout from '../components/layout/PageLayout'; // Adjust path as needed
import {useAuth} from '../hooks/auth/useAuth'
import { useAuthStore } from '@/stores/auth-store';

const VimsHome = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);

    const {user: currentUser} = useAuth();
    

    useEffect(() => {
        
        if (!currentUser) {
            navigate('/login', { replace: true });
        } else {
            setUser(currentUser);
        }
    }, [navigate]);

    const handleLogout = async () => {
        await useAuthStore.getState().logout();
        navigate('/login', { replace: true });
    };

    const userName = user?.display_name || user?.employee_id || user?.crew_id;

    if (!user) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500 mb-4"></div>
                    <p className="text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <PageLayout
            userName={userName}
            onLogout={handleLogout}
            customTitle="VIMS"
            showBreadcrumbs={true}
        >
            <div className="h-full flex items-center justify-center bg-white rounded shadow">
                <div className="text-center">
                    <h1 className="text-2xl font-semibold mb-2">Welcome to VIMS</h1>
                    <p className="text-gray-600">
                        Select a module from the sidebar to get started.
                    </p>
                </div>
            </div>
        </PageLayout>
    );
};

export default VimsHome;
