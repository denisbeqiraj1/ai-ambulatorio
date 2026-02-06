import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Search from './pages/Search';
import Login from './pages/Login';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Search />
            </ProtectedRoute>
          }
        />
        {/* Redirect unknown routes to home (which redirects to login if needed) */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;