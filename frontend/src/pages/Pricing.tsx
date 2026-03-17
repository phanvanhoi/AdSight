import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Check, Loader2, ExternalLink, CreditCard, X } from 'lucide-react'
import {
  createCheckoutSession,
  createPortalSession,
  createVNPaySession,
  createMoMoSession,
  getMe,
} from '../api/billing'

const plans = [
  {
    id: 'free' as const,
    name: 'Free',
    price: '$0',
    priceVND: '',
    features: [
      '50 searches/ngày',
      '1 nền tảng',
      '3 boards, 50 saved ads',
      'Data 7 ngày',
      'Export CSV (100 rows)',
    ],
  },
  {
    id: 'pro' as const,
    name: 'Pro',
    price: '$29',
    priceVND: '699,000d',
    popular: true,
    features: [
      'Unlimited searches',
      'Tất cả nền tảng',
      'Unlimited boards & saved ads',
      'Data 90 ngày',
      'AI Analysis: 50 credits/tháng',
      '5 competitor alerts',
      'Export 10,000 rows',
    ],
  },
  {
    id: 'agency' as const,
    name: 'Agency',
    price: '$79',
    priceVND: '1,899,000d',
    features: [
      'Tất cả tính năng Pro',
      'AI Analysis: 500 credits/tháng',
      '50 competitor alerts',
      'Full data history',
      'Export 100,000 rows',
      'Priority support',
    ],
  },
]

export default function Pricing() {
  const [loading, setLoading] = useState<string | null>(null)
  const [selectedPlan, setSelectedPlan] = useState<'pro' | 'agency' | null>(null)

  const { data: profile } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
  })

  const currentTier = profile?.tier || 'free'

  const handleStripe = async (plan: 'pro' | 'agency') => {
    setLoading('stripe')
    try {
      const { checkout_url } = await createCheckoutSession(plan)
      window.location.href = checkout_url
    } catch {
      setLoading(null)
    }
  }

  const handleVNPay = async (plan: 'pro' | 'agency') => {
    setLoading('vnpay')
    try {
      const { payment_url } = await createVNPaySession(plan)
      window.location.href = payment_url
    } catch {
      setLoading(null)
    }
  }

  const handleMoMo = async (plan: 'pro' | 'agency') => {
    setLoading('momo')
    try {
      const { pay_url } = await createMoMoSession(plan)
      window.location.href = pay_url
    } catch {
      setLoading(null)
    }
  }

  const handleManage = async () => {
    setLoading('manage')
    try {
      const { portal_url } = await createPortalSession()
      window.location.href = portal_url
    } catch {
      setLoading(null)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900">Bảng giá</h1>
        <p className="text-gray-500 mt-2">Chọn gói phù hợp với nhu cầu của bạn</p>
      </div>

      {/* Usage summary */}
      {profile && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Sử dụng hôm nay</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Tìm kiếm</p>
              <p className="font-semibold">
                {profile.usage.searches.used}/{profile.usage.searches.limit === -1 ? '\u221e' : profile.usage.searches.limit}
              </p>
            </div>
            <div>
              <p className="text-gray-500">AI Credits</p>
              <p className="font-semibold">
                {profile.usage.ai_credits.used}/{profile.usage.ai_credits.limit === 0 ? '\u2014' : profile.usage.ai_credits.limit}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Boards</p>
              <p className="font-semibold">
                {profile.usage.boards.limit === -1 ? 'Unlimited' : `Tối đa ${profile.usage.boards.limit}`}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Saved Ads</p>
              <p className="font-semibold">
                {profile.usage.saved_ads.limit === -1 ? 'Unlimited' : `Tối đa ${profile.usage.saved_ads.limit}`}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Plans */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const isCurrent = currentTier === plan.id
          const isUpgrade = !isCurrent && plan.id !== 'free'

          return (
            <div
              key={plan.id}
              className={`p-6 rounded-xl border-2 relative ${
                plan.popular ? 'border-primary-500' : 'border-gray-200'
              }`}
            >
              {plan.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-primary-600 text-white text-xs font-semibold rounded-full">
                  Phổ biến
                </span>
              )}

              <h3 className="font-bold text-lg">{plan.name}</h3>
              <p className="text-3xl font-bold mt-2">
                {plan.price}
                <span className="text-sm text-gray-400 font-normal">/tháng</span>
              </p>
              {plan.priceVND && (
                <p className="text-sm text-gray-500 mt-0.5">{plan.priceVND}/tháng</p>
              )}

              <ul className="mt-4 space-y-2 text-sm text-gray-600">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <Check size={16} className="text-green-500 mt-0.5 flex-shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>

              {isCurrent ? (
                <div className="mt-6">
                  <span className="block text-center py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium">
                    Gói hiện tại
                  </span>
                  {plan.id !== 'free' && profile?.subscription_status === 'active' && (
                    <button
                      onClick={handleManage}
                      disabled={loading === 'manage'}
                      className="flex items-center justify-center gap-1.5 w-full mt-2 py-2 text-sm text-primary-600 hover:text-primary-700"
                    >
                      {loading === 'manage' ? <Loader2 size={14} className="animate-spin" /> : <ExternalLink size={14} />}
                      Quản lý subscription
                    </button>
                  )}
                </div>
              ) : isUpgrade ? (
                <button
                  onClick={() => setSelectedPlan(plan.id as 'pro' | 'agency')}
                  className={`block mt-6 w-full text-center py-2 rounded-lg text-sm font-medium transition-colors ${
                    plan.popular
                      ? 'bg-primary-600 text-white hover:bg-primary-700'
                      : 'border border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  Nâng cấp
                </button>
              ) : (
                <div className="mt-6">
                  <span className="block text-center py-2 text-gray-400 text-sm">&mdash;</span>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Payment method modal */}
      {selectedPlan && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 shadow-lg max-w-sm w-full space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Chọn phương thức thanh toán</h3>
              <button onClick={() => { setSelectedPlan(null); setLoading(null) }} className="p-1 text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <p className="text-sm text-gray-500">
              Gói {selectedPlan === 'pro' ? 'Pro — 699,000đ' : 'Agency — 1,899,000đ'}/tháng
            </p>

            <button
              onClick={() => handleStripe(selectedPlan)}
              disabled={loading === 'stripe'}
              className="w-full flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <CreditCard size={20} className="text-primary-600 flex-shrink-0" />
              <div className="text-left flex-1">
                <p className="font-medium text-sm">Thẻ quốc tế (Visa/Mastercard)</p>
                <p className="text-xs text-gray-400">Tự động gia hạn hàng tháng</p>
              </div>
              {loading === 'stripe' && <Loader2 size={16} className="animate-spin text-gray-400" />}
            </button>

            <button
              onClick={() => handleVNPay(selectedPlan)}
              disabled={loading === 'vnpay'}
              className="w-full flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="w-5 h-5 bg-red-500 rounded text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0">VN</div>
              <div className="text-left flex-1">
                <p className="font-medium text-sm">VNPay (QR / ATM nội địa)</p>
                <p className="text-xs text-gray-400">30+ ngân hàng Việt Nam</p>
              </div>
              {loading === 'vnpay' && <Loader2 size={16} className="animate-spin text-gray-400" />}
            </button>

            <button
              onClick={() => handleMoMo(selectedPlan)}
              disabled={loading === 'momo'}
              className="w-full flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="w-5 h-5 bg-pink-500 rounded text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0">M</div>
              <div className="text-left flex-1">
                <p className="font-medium text-sm">Ví MoMo</p>
                <p className="text-xs text-gray-400">Thanh toán nhanh qua ví điện tử</p>
              </div>
              {loading === 'momo' && <Loader2 size={16} className="animate-spin text-gray-400" />}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
