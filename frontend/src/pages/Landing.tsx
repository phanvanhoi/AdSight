import { Link } from 'react-router-dom'
import { Search, Zap, Bell, TrendingUp, BarChart3, Shield } from 'lucide-react'

const features = [
  {
    icon: Search,
    title: 'Tìm kiếm ads thông minh',
    desc: 'Tìm ads đang chạy trên Facebook, TikTok tại Việt Nam với bộ lọc mạnh mẽ và tìm kiếm tiếng Việt.',
  },
  {
    icon: Zap,
    title: 'AI Phân tích Creative',
    desc: 'AI tự động phân tích: hook, CTA, emotional trigger, gợi ý cải thiện. (Coming Phase 2)',
  },
  {
    icon: Bell,
    title: 'Theo dõi đối thủ tự động',
    desc: 'Nhận thông báo khi đối thủ launch ads mới. Không bao giờ bỏ lỡ. (Coming Phase 2)',
  },
  {
    icon: TrendingUp,
    title: 'Xu hướng Ads Việt Nam',
    desc: 'Phát hiện xu hướng ads mới nhất tại thị trường Việt Nam trước mọi người.',
  },
  {
    icon: BarChart3,
    title: 'TikTok Shop Analytics',
    desc: 'Phân tích ads + shop + affiliate trên TikTok Shop VN. (Coming Phase 3)',
  },
  {
    icon: Shield,
    title: 'Miễn phí để bắt đầu',
    desc: '50 searches/ngày, 3 boards, export CSV. Không cần thẻ tín dụng.',
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary-950 via-surface-900 to-primary-900" />

        {/* Header */}
        <header className="relative z-10">
          <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">AD</span>
              </div>
              <span className="font-bold text-xl text-white">AdSight</span>
            </div>
            <div className="flex items-center gap-3">
              <Link to="/login" className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white rounded-lg">
                Đăng nhập
              </Link>
              <Link to="/register" className="px-4 py-2 text-sm font-medium text-white bg-primary-500 hover:bg-primary-400 rounded-lg">
                Đăng ký miễn phí
              </Link>
            </div>
          </div>
        </header>

        <div className="relative max-w-6xl mx-auto px-4 py-24 text-center">
          {/* Status badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white/10 backdrop-blur-sm rounded-full text-sm text-primary-200 mb-8">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            Đang theo dõi 500K+ ads
          </div>

          <h1 className="text-4xl md:text-6xl font-bold text-white leading-tight">
            Biết đối thủ chạy ads gì
            <br />
            <span className="bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
              trước khi họ biết bạn đang theo dõi
            </span>
          </h1>

          <p className="mt-6 text-lg text-gray-300 max-w-2xl mx-auto">
            Nền tảng Ad Intelligence đầu tiên tập trung vào thị trường Việt Nam.
            Tìm kiếm, phân tích và theo dõi quảng cáo trên Facebook, TikTok và Google.
          </p>

          <div className="mt-10 flex items-center justify-center gap-4">
            <Link to="/register" className="px-8 py-3.5 bg-primary-500 text-white font-semibold rounded-xl hover:bg-primary-400 text-lg shadow-lg shadow-primary-500/25 transition-all">
              Bắt đầu miễn phí
            </Link>
            <Link to="/search" className="px-8 py-3.5 bg-white/10 backdrop-blur-sm text-white font-semibold rounded-xl hover:bg-white/20 text-lg transition-all">
              Thử tìm kiếm
            </Link>
          </div>

          <p className="mt-5 text-sm text-gray-400">Free tier: 50 searches/ngày. Không cần thẻ tín dụng.</p>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-bold text-center text-gray-900 mb-12">Tại sao chọn AdSight?</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => (
            <div key={feature.title} className="p-6 rounded-xl border border-gray-200 hover:shadow-soft transition-shadow">
              <feature.icon className="text-primary-600 mb-4" size={32} />
              <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-sm text-gray-500">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-bold text-center text-gray-900 mb-12">Bảng giá</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {/* Free */}
          <div className="p-6 rounded-xl border-2 border-gray-200">
            <h3 className="font-bold text-lg">Free</h3>
            <p className="text-3xl font-bold mt-2">$0<span className="text-sm text-gray-400 font-normal">/tháng</span></p>
            <ul className="mt-4 space-y-2 text-sm text-gray-600">
              <li>50 searches/ngày</li>
              <li>1 nền tảng</li>
              <li>3 boards, 50 saved ads</li>
              <li>Data 7 ngày</li>
              <li>Export CSV (100 rows)</li>
            </ul>
            <Link to="/register" className="block mt-6 text-center py-2 border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50">
              Bắt đầu
            </Link>
          </div>

          {/* Pro */}
          <div className="p-6 rounded-xl border-2 border-primary-500 relative">
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-primary-600 text-white text-xs font-semibold rounded-full">
              Phổ biến
            </span>
            <h3 className="font-bold text-lg">Pro</h3>
            <p className="text-3xl font-bold mt-2">$29<span className="text-sm text-gray-400 font-normal">/tháng</span></p>
            <ul className="mt-4 space-y-2 text-sm text-gray-600">
              <li>Unlimited searches</li>
              <li>Tất cả nền tảng</li>
              <li>Unlimited boards</li>
              <li>Data 90 ngày</li>
              <li>AI Analysis: 50 credits</li>
              <li>5 competitor alerts</li>
            </ul>
            <Link to="/register" className="block mt-6 w-full text-center py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
              Bắt đầu dùng thử
            </Link>
          </div>

          {/* Agency */}
          <div className="p-6 rounded-xl border-2 border-gray-200">
            <h3 className="font-bold text-lg">Agency</h3>
            <p className="text-3xl font-bold mt-2">$79<span className="text-sm text-gray-400 font-normal">/tháng</span></p>
            <ul className="mt-4 space-y-2 text-sm text-gray-600">
              <li>Tất cả tính năng Pro</li>
              <li>AI Analysis: 500 credits</li>
              <li>Team 5 thành viên</li>
              <li>API access</li>
              <li>Client reporting</li>
              <li>Priority support</li>
            </ul>
            <Link to="/register" className="block mt-6 w-full text-center py-2 border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50">
              Bắt đầu dùng thử
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8">
        <div className="max-w-6xl mx-auto px-4 text-center text-sm text-gray-400">
          <p>AdSight — Nền tảng Ad Intelligence cho thị trường Việt Nam</p>
        </div>
      </footer>
    </div>
  )
}
