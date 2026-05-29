import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useSession } from '@/store/SessionContext'

export function AuthGuard() {
  const session = useSession()
  const location = useLocation()

  if (!session.isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
