import { Navigate, RouterProvider, createBrowserRouter } from 'react-router-dom'
import { AuthGuard } from '@/components/layout/AuthGuard'
import { useSession, SessionProvider } from '@/store/SessionContext'
import Chat from '@/pages/Chat'
import Login from '@/pages/Login'
import Register from '@/pages/Register'

function RootRedirect() {
  const session = useSession()
  return <Navigate to={session.getDefaultRedirect()} replace />
}

const router = createBrowserRouter([
  { path: '/', element: <RootRedirect /> },
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
  {
    element: <AuthGuard />,
    children: [{ path: '/chat', element: <Chat /> }],
  },
  { path: '*', element: <RootRedirect /> },
])

export default function App() {
  return (
    <SessionProvider>
      <RouterProvider router={router} />
    </SessionProvider>
  )
}
