import { useQuery } from '@tanstack/react-query'
import { BarChart3, TrendingUp, Users, Zap } from 'lucide-react'
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
} from 'recharts'
import { getDashboardOverview, getTrendingAds } from '../api/dashboard'
import AdGrid from '../components/search/AdGrid'

const CHART_COLORS = ['#4f46e5', '#06b6d4', '#f43f5e', '#f59e0b', '#10b981']

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
    { label: 'Tổng ads', value: overview?.total_ads?.toLocaleString() || '0', icon: BarChart3, color: 'text-blue-600 bg-blue-100' },
    { label: 'Ads active', value: overview?.active_ads?.toLocaleString() || '0', icon: Zap, color: 'text-green-600 bg-green-100' },
    { label: 'Mới 24h', value: overview?.ads_last_24h?.toLocaleString() || '0', icon: TrendingUp, color: 'text-purple-600 bg-purple-100' },
    { label: 'Platforms', value: Object.keys(overview?.platforms || {}).length || '0', icon: Users, color: 'text-orange-600 bg-orange-100' },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Tổng quan thị trường quảng cáo Việt Nam</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border border-gray-100 p-5 shadow-card hover:shadow-soft transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 font-medium">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
              </div>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${stat.color}`}>
                <stat.icon size={22} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Platform breakdown — PieChart */}
      {overview?.platforms && Object.keys(overview.platforms).length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-card">
          <h2 className="font-semibold text-gray-900 mb-4">Phân bổ theo nền tảng</h2>
          <div className="flex items-center gap-8">
            <div className="w-48 h-48">
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={Object.entries(overview.platforms).map(([name, value]) => ({ name, value }))}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {Object.keys(overview.platforms).map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1 space-y-2">
              {Object.entries(overview.platforms).map(([platform, count], i) => (
                <div key={platform} className="flex items-center gap-3">
                  <span className="w-3 h-3 rounded-full" style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
                  <span className="text-sm text-gray-700 flex-1 capitalize">{platform}</span>
                  <span className="text-sm font-semibold text-gray-900">{(count as number).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Trending Ads */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Trending Ads tuần này</h2>
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
