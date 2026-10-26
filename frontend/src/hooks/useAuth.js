/**
 * useAuth — convenience hook to consume AuthContext.
 */

/* it helps in authentication by providing access to the authentication context, allowing components to easily access user information and authentication status. */
import { useContext } from 'react';
import AuthContext from '../context/AuthContext';

export default function useAuth() {
  return useContext(AuthContext);
}
