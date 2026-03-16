import { Link } from 'react-router-dom'
import { Search, Zap, Bell, TrendingUp, BarChart3, Shield } from 'lucide-react'

const features = [
  {
    icon: Search,
    title: 'Tim kiem ads thong minh',
    desc: 'Tim ads dang chay tren Facebook, TikTok tai Viet Nam voi bo loc manh me va tim kiem tieng Viet.',
  },
  {
    icon: Zap,
    title: 'AI Phan tich Creative',
    desc: 'AI tu dong phan tich: hook, CTA, emotional trigger, goi y cai thien. (Coming Phase 2)',
  },
  {
    icon: Bell,
    title: 'Theo doi doi thu tu dong',
    desc: 'Nhan thong bao khi doi thu launch ads moi. Khong bao gio bo lo. (Coming Phase 2)',
  },
  {
    icon: TrendingUp,
    title: 'Trend Ads Viet Nam',
    desc: 'Phat hien xu huong ads moi nhat tai thi truong Viet Nam truoc moi nguoi.',
  },
  {
    icon: BarChart3,
    title: 'TikTok Shop Analytics',
    desc: 'Phan tich ads + shop + affiliate tren TikTok Shop VN. (Coming Phase 3)',
  },
  {
    icon: Shield,
    title: 'Mien phi de bat dau',
    desc: '50 searches/ngay, 3 boards, export CSV. Khong can the tin dung.',
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AD</span>
            </div>
            <span className="font-bold text-xl">AdSight</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg">
              Dang nhap
            </Link>
            <Link to="/register" className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg">
              Dang ky mien phi
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-4 py-20 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight">
          Biet doi thu chay ads gi
          <br />
          <span className="text-primary-600">truoc khi ho biet ban dang theo doi</span>
        </h1>
        <p className="mt-6 text-lg text-gray-500 max-w-2xl mx-auto">
          Nen tang Ad Intelligence dau tien tap trung vao thi truong Viet Nam.
          Tim kiem, phan tich va theo doi quang cao tren Facebook va TikTok.
        </p>
        <div className="mt-8 flex items-center justify-center gap-4">
          <Link
            to="/register"
            className="px-8 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 text-lg"
          >
            Bat dau mien phi
          </Link>
          <Link
            to="/search"
            className="px-8 py-3 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200 text-lg"
          >
            Thu tim kiem
          </Link>
        </div>
        <p className="mt-4 text-sm text-gray-400">Free tier: 50 searches/ngay. Khong can the tin dung.</p>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-bold text-center text-gray-900 mb-12">Tai sao chon AdSight?</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => (
            <div key={feature.title} className="p-6 rounded-xl border border-gray-200 hover:shadow-md transition-shadow">
              <feature.icon className="text-primary-600 mb-4" size={32} />
              <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-sm text-gray-500">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-bold text-center text-gray-900 mb-12">Bang gia</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {/* Free */}
          <div className="p-6 rounded-xl border-2 border-gray-200">
            <h3 className="font-bold text-lg">Free</h3>
            <p className="text-3xl font-bold mt-2">$0<span className="text-sm text-gray-400 font-normal">/thang</span></p>
            <ul className="mt-4 space-y-2 text-sm text-gray-600">
              <li>50 searches/ngay</li>
              <li>1 nen tang</li>
              <li>3 boards, 50 saved ads</li>
              <li>Data 7 ngay</li>
              <li>Export CSV (100 rows)</li>
            </ul>
            <Link to="/register" className="block mt-6 text-center py-2 border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50">
              Bat dau
            </Link>
          </div>

          {/* Pro */}
          <div className="p-6 rounded-xl border-2 border-primary-500 relative">
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-primary-600 text-white text-xs font-semibold rounded-full">
              Pho bien
            </span>
            <h3 className="font-bold text-lg">Pro</h3>
            <p className="text-3xl font-bold mt-2">$29<span className="text-sm text-gray-400 font-normal">/thang</span></p>
            <ul className="mt-4 space-y-2 text-sm text-gray-600">
              <li>Unlimited searches</li>
              <li>Tat ca nen tang</li>
              <li>Unlimited boards</li>
              <li>Data 90 ngay</li>
              <li>AI Analysis: 50 credits</li>
              <li>5 competitor alerts</li>
            </ul>
            <button className="block mt-6 w-full text-center py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
              Coming soon
            </button>
          </div>

          {/* Agency */}
          <div className="p-6 rounded-xl border-2 border-gray-200">
            <h3 className="font-bold text-lg">Agency</h3>
            <p className="text-3xl font-bold mt-2">$79<span className="text-sm text-gray-400 font-normal">/thang</span></p>
            <ul className="mt-4 space-y-2 text-sm text-gray-600">
              <li>Tat ca tinh nang Pro</li>
              <li>AI Analysis: 500 credits</li>
              <li>Team 5 thanh vien</li>
              <li>API access</li>
              <li>Client reporting</li>
              <li>Priority support</li>
            </ul>
            <button className="block mt-6 w-full text-center py-2 border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50">
              Coming soon
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8">
        <div className="max-w-6xl mx-auto px-4 text-center text-sm text-gray-400">
          <p>AdSight - Nen tang Ad Intelligence cho thi truong Viet Nam</p>
        </div>
      </footer>
    </div>
  )
}
