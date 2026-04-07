/**
 * useAuth hook — single source of truth.
 * Re-exported from AuthContext so there is only one implementation.
 * The guard (throws if used outside <AuthProvider>) lives in AuthContext.tsx.
 */
export { useAuth } from '@/contexts/AuthContext';
