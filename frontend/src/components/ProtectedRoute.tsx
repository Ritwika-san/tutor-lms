import { Navigate } from 'react-router-dom';
import { User } from '../api/authAPI';

interface ProtectedRouteProps {
  element: React.ReactElement;
}

/**
 * ProtectedRoute component that checks if user is authenticated.
 * If not, redirects to login page.
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ element }) => {
  const userString = localStorage.getItem('user');
  const token = localStorage.getItem('accessToken');

  if (!userString || !token) {
    return <Navigate to="/login" replace />;
  }

  try {
    const user: User = JSON.parse(userString);
    if (!user || !user.id) {
      return <Navigate to="/login" replace />;
    }
  } catch {
    return <Navigate to="/login" replace />;
  }

  return element;
};
