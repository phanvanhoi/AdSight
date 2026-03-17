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
import Pricing from './pages/Pricing'
import BillingSuccess from './pages/BillingSuccess'
import Alerts from './pages/Alerts'
import Settings from './pages/Settings'

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
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/billing/success" element={<BillingSuccess />} />
        <Route path="/billing/vnpay-return" element={<BillingSuccess />} />
        <Route path="/billing/momo-return" element={<BillingSuccess />} />
      </Route>
    </Routes>
  )
}
