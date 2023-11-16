import { createContext } from "react";
import { User } from "./useUser";

interface AuthContext {
  user: User  | undefined;
  setUser: (user: User | undefined) => void;
}

export const AuthContext = createContext<AuthContext>({
  user: undefined,
  setUser: () => { },
});