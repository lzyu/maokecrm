import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import AppLayout from './components/layout/AppLayout'
import LoginPage from './pages/auth/LoginPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import CustomerListPage from './pages/customers/CustomerListPage'
import CustomerDetailPage from './pages/customers/CustomerDetailPage'
import UserListPage from './pages/users/UserListPage'
import FollowupListPage from './pages/followups/FollowupListPage'
import OpportunityListPage from './pages/opportunities/OpportunityListPage'
import ServiceRecordListPage from './pages/services/ServiceRecordListPage'
import ReminderListPage from './pages/reminders/ReminderListPage'
import ImportPage from './pages/imports/ImportPage'
import AuditLogPage from './pages/audit/AuditLogPage'

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

// Admin route wrapper
function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  const isAdmin = user?.role_name === 'admin' || user?.role_name === 'super_admin'
  if (!isAdmin) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="customers" element={<CustomerListPage />} />
          <Route path="customers/:id" element={<CustomerDetailPage />} />
          <Route path="followups" element={<FollowupListPage />} />
          <Route path="opportunities" element={<OpportunityListPage />} />
          <Route path="services" element={<ServiceRecordListPage />} />
          <Route path="reminders" element={<ReminderListPage />} />
          <Route
            path="imports"
            element={
              <AdminRoute>
                <ImportPage />
              </AdminRoute>
            }
          />
          <Route
            path="users"
            element={
              <AdminRoute>
                <UserListPage />
              </AdminRoute>
            }
          />
          <Route
            path="audit"
            element={
              <AdminRoute>
                <AuditLogPage />
              </AdminRoute>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
