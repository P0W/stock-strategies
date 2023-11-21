import { useEffect, useRef, useState } from 'react';
import { useLocalStorage } from './useLocalStorage';
import { User } from './useUser';

const TIMEOUT_DURATION = 60 * 60 * 1000; // 1 hour

export const useInactivityLogout = (user: User | undefined) => {
    const logoutTimerRef = useRef<NodeJS.Timeout | null>(null);
    const { setItem, getItem, removeItem } = useLocalStorage();
    const [expired, setExpired] = useState(false);

    const cleanup = () => {
        window.removeEventListener('mousemove', resetLogoutTimer);
        window.removeEventListener('keydown', resetLogoutTimer);
        removeItem('logoutTimer');
        if (logoutTimerRef.current) {
            clearTimeout(logoutTimerRef.current);
            logoutTimerRef.current = null;
        }
        setExpired(true);
    };

    const startLogoutTimer = () => {
        const expirationTime = Date.now() + TIMEOUT_DURATION;
        setItem('logoutTimer', expirationTime.toString());

        logoutTimerRef.current = setTimeout(() => {
            cleanup(); // Log out the user
        }, TIMEOUT_DURATION);
    };

    const resetLogoutTimer = () => {
        if (logoutTimerRef.current) {
            clearTimeout(logoutTimerRef.current);
            logoutTimerRef.current = null;
        }

        startLogoutTimer();
    };

    useEffect(() => {
        const logoutTimer = getItem('logoutTimer');
        if (logoutTimer && Date.now() > Number(logoutTimer)) {
            // If the current time is past the logout time, log out the user
            cleanup();
        } else if (user) {
            // Start the logout timer when the user logs in
            startLogoutTimer();
        }
    }, [user]);

    useEffect(() => {
        // Reset the logout timer whenever there's any activity
        if (user) {
            window.addEventListener('mousemove', resetLogoutTimer);
            window.addEventListener('keydown', resetLogoutTimer);
        }

        return () => {
            window.removeEventListener('mousemove', resetLogoutTimer);
            window.removeEventListener('keydown', resetLogoutTimer);
        };
    }, [user]);

    return { cleanup, expired };
};