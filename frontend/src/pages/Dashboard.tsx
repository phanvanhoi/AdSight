import { useQuery } from '@tanstack/react-query'
import { BarChart3, TrendingUp, Users, Zap } from 'lucide-react'
import { getDashboardOverview, getTrendingAds } from '../api/dashboard'
import AdGrid from '../components/search/AdGrid'

export default function Dashboard() {
  const { data: overview } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: getDashboardOverview,
  })

  const { data: trending, isLoading } = useQuery({
    queryKey: ['trending-ads'],
    queryFn: getTrendingAds,
  })

  const stats = [
    { label: 'Tong ads', value: overview?.total_ads?.toLocaleString() || '0', icon: BarChart3, color: 'text-blue-600 bg-blue-100' },
    { label: 'Ads active', value: overview?.active_ads?.toLocaleString() || '0', icon: Zap, color: 'text-green-600 bg-green-100' },
    { label: 'Moi 24h', value: overview?.ads_last_24h?.toLocaleString() || '0', icon: TrendingUp, color: 'text-purple-600 bg-purple-100' },
    { label: 'Platforms', value: Object.keys(overview?.platforms || {}).length || '0', icon: Users, color: 'text-orange-600 bg-orange-100' },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Tong quan thi truong quang cao Viet Nam</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${stat.color}`}>
                <stat.icon size={20} />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                <p className="text-xs text-gray-500">{stat.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Platform breakdown */}
      {overview?.platforms && Object.keys(overview.platforms).length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Ads theo nen tang</h2>
          <div className="space-y-3">
            {Object.entries(overview.platforms).map(([platform, count]) => {
              const total = overview.total_ads || 1
              const pct = Math.round(((count as number) / total) * 100)
              return (
                <div key={platform} className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-700 w-20">{platform}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-2.5">
                    <div
                      className="bg-primary-500 h-2.5 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-500 w-20 text-right">
                    {(count as number).toLocaleString()} ({pct}%)
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Trending Ads */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Trending Ads tuan nay</h2>
        <AdGrid
          ads={(trending || []).map((ad: any) => ({
            ...ad,
            days_running: 0,
          }))}
          loading={isLoading}
        />
      </div>
    </div>
  )
}
