import { useContext } from "react";
import { AuthContext } from "./AuthContext";
import { useLocalStorage } from "./useLocalStorage";

export interface User {
    fullName?: string;
    email?: string;
    phoneNumber?: string;
    num_stocks?: number;
    investment?: number;
}

export const useUser = () => {
    const { user, setUser } = useContext(AuthContext);
    const { setItem } = useLocalStorage();

    const addUser = (user: User) => {
        setUser(user);
        setItem("user", JSON.stringify(user));
    };

    const removeUser = () => {
        setUser(undefined);
        setItem("user", "");
    };

    return { user, addUser, removeUser };
};