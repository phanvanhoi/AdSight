import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Landing from './pages/Landing'
import Search from './pages/Search'
import AdDetailPage from './pages/AdDetailPage'
import Dashboard from './pages/Dashboard'
import Boards from './pages/Boards'
import TikTokShopPage from './pages/TikTokShopPage'
import AdvertisersPage from './pages/AdvertisersPage'
import AdvertiserDetailPage from './pages/AdvertiserDetailPage'
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
        <Route path="/tiktok-shop" element={<TikTokShopPage />} />
        <Route path="/advertisers" element={<AdvertisersPage />} />
        <Route path="/advertisers/:id" element={<AdvertiserDetailPage />} />
      </Route>
    </Routes>
  )
}
