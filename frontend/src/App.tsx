import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Landing from './pages/Landing'
import Search from './pages/Search'
import AdDetailPage from './pages/AdDetailPage'
import Dashboard from './pages/Dashboard'
import Boards from './pages/Boards'
import Login from './pages/Login'
import Register from './pages/Register'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<Layout />}>
        <Route path="/search" element={<Search />} />
        <Route path="/ads/:id" element={<AdDetailPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/boards" element={<Boards />} />
      </Route>
    </Routes>
  )
}
