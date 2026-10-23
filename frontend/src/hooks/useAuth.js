/**
 * useAuth — convenience hook to consume AuthContext.
 */
import { useContext } from 'react';
import AuthContext from '../context/AuthContext';

export default function useAuth() {
  return useContext(AuthContext);
}
