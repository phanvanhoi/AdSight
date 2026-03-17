import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, Loader2, AlertCircle, Link as LinkIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getAIAnalysis } from '../../api/ads'
import type { AIAnalysis } from '../../types/ad'
import { AxiosError } from 'axios'

function ScoreBar({ score, max = 10 }: { score: number; max?: number }) {
  const pct = (score / max) * 100
  const color =
    score <= 3 ? 'bg-red-500' : score <= 6 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold text-gray-600 w-8 text-right">{score}/{max}</span>
    </div>
  )
}

export default function AIAnalysisPanel({ adId }: { adId: string }) {
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null)
  const [cached, setCached] = useState(false)

  const mutation = useMutation({
    mutationFn: () => getAIAnalysis(adId),
    onSuccess: (data) => {
      setAnalysis(data.analysis)
      setCached(data.cached)
    },
  })

  const error = mutation.error as AxiosError<{ detail: { error: string; message: string; upgrade_url?: string } }> | null
  const errorData = error?.response?.data?.detail
  const isFreeGate = error?.response?.status === 403
  const isCreditsExhausted = error?.response?.status === 429

  // Not yet analyzed — show trigger button
  if (!analysis && !mutation.isPending && !error) {
    return (
      <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
            <Sparkles size={14} className="text-primary-500" />
            Phân tích AI
          </h3>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          Phân tích chi tiết ad creative: hook, emotional triggers, copy, CTA, target audience...
        </p>
        <button
          onClick={() => mutation.mutate()}
          className="w-full py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors flex items-center justify-center gap-2"
        >
          <Sparkles size={16} />
          Phân tích ngay
        </button>
        <p className="text-xs text-gray-400 mt-2 text-center">Tốn 1 AI credit</p>
      </div>
    )
  }

  // Loading
  if (mutation.isPending) {
    return (
      <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-card">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Loader2 size={16} className="animate-spin text-primary-500" />
          Đang phân tích... (10-20 giây)
        </div>
      </div>
    )
  }

  // Error states
  if (error) {
    return (
      <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-card">
        <div className="flex items-center gap-2 text-sm text-red-600 mb-2">
          <AlertCircle size={16} />
          {isFreeGate
            ? 'AI Analysis chỉ có trong gói Pro trở lên'
            : isCreditsExhausted
              ? (typeof errorData === 'object' ? errorData.message : 'Bạn đã hết AI credits tháng này')
              : 'Phân tích thất bại, thử lại sau'}
        </div>
        {isFreeGate && (
          <Link to="/pricing" className="flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium">
            <LinkIcon size={14} />
            Nâng cấp ngay
          </Link>
        )}
        {!isFreeGate && !isCreditsExhausted && (
          <button
            onClick={() => mutation.mutate()}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            Thử lại
          </button>
        )}
      </div>
    )
  }

  if (!analysis) return null

  // Render full analysis
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-card overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
          <Sparkles size={14} className="text-primary-500" />
          Phân tích AI
        </h3>
        {cached && (
          <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded-full">Cached</span>
        )}
      </div>

      <div className="p-5 space-y-5">
        {/* Summary */}
        <p className="text-sm text-gray-700 leading-relaxed">{analysis.summary}</p>

        {/* Hook + Target Audience grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Hook Analysis */}
          <div className="p-3 bg-blue-50/50 rounded-lg space-y-2">
            <h4 className="text-xs font-semibold text-blue-700 uppercase">Hook Analysis</h4>
            <span className="inline-block px-2.5 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
              {analysis.hook_analysis.hook_type}
            </span>
            {analysis.hook_analysis.hook_text && (
              <p className="text-xs text-gray-600 italic">"{analysis.hook_analysis.hook_text}"</p>
            )}
            <ScoreBar score={analysis.hook_analysis.effectiveness} />
            <p className="text-xs text-gray-500">{analysis.hook_analysis.explanation}</p>
          </div>

          {/* Target Audience */}
          <div className="p-3 bg-violet-50/50 rounded-lg space-y-2">
            <h4 className="text-xs font-semibold text-violet-700 uppercase">Target Audience</h4>
            <p className="text-sm font-medium text-gray-700">{analysis.target_audience.primary}</p>
            <p className="text-xs text-gray-500">{analysis.target_audience.demographics}</p>
            <p className="text-xs text-gray-500">{analysis.target_audience.psychographics}</p>
          </div>
        </div>

        {/* Emotional triggers */}
        {analysis.emotional_triggers?.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">Emotional Triggers</h4>
            <div className="flex flex-wrap gap-1.5">
              {analysis.emotional_triggers.map((t) => (
                <span key={t} className="px-2.5 py-0.5 bg-fuchsia-50 text-fuchsia-700 text-xs font-medium rounded-full">{t}</span>
              ))}
            </div>
          </div>
        )}

        {/* Copy + CTA grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Copy Analysis */}
          <div className="p-3 bg-gray-50 rounded-lg space-y-2">
            <h4 className="text-xs font-semibold text-gray-500 uppercase">Copy Analysis</h4>
            <span className="inline-block px-2.5 py-0.5 bg-gray-200 text-gray-600 text-xs font-medium rounded-full">
              {analysis.copy_analysis.tone}
            </span>
            <div>
              <p className="text-xs text-gray-400 mb-1">Readability</p>
              <ScoreBar score={analysis.copy_analysis.readability} />
            </div>
            {analysis.copy_analysis.key_benefits?.length > 0 && (
              <div>
                <p className="text-xs text-gray-400 mb-1">Key Benefits</p>
                <ul className="text-xs text-gray-600 space-y-0.5">
                  {analysis.copy_analysis.key_benefits.map((b) => (
                    <li key={b}>• {b}</li>
                  ))}
                </ul>
              </div>
            )}
            {analysis.copy_analysis.power_words?.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {analysis.copy_analysis.power_words.map((w) => (
                  <span key={w} className="px-2 py-0.5 bg-primary-50 text-primary-700 text-xs font-medium rounded-full">{w}</span>
                ))}
              </div>
            )}
          </div>

          {/* CTA Analysis */}
          <div className="p-3 bg-orange-50/50 rounded-lg space-y-2">
            <h4 className="text-xs font-semibold text-orange-700 uppercase">CTA Analysis</h4>
            {analysis.cta_analysis.cta_text && (
              <p className="text-sm font-medium text-gray-700">"{analysis.cta_analysis.cta_text}"</p>
            )}
            <div>
              <p className="text-xs text-gray-400 mb-1">Strength</p>
              <ScoreBar score={analysis.cta_analysis.cta_strength} />
            </div>
            {analysis.cta_analysis.suggestion && (
              <p className="text-xs text-gray-500">Gợi ý: {analysis.cta_analysis.suggestion}</p>
            )}
          </div>
        </div>

        {/* Strengths + Weaknesses */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {analysis.strengths?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-green-600 uppercase mb-2">Điểm mạnh</h4>
              <ul className="space-y-1">
                {analysis.strengths.map((s) => (
                  <li key={s} className="text-xs px-2.5 py-1 bg-green-50 text-green-700 rounded-md">{s}</li>
                ))}
              </ul>
            </div>
          )}
          {analysis.weaknesses?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-red-600 uppercase mb-2">Điểm yếu</h4>
              <ul className="space-y-1">
                {analysis.weaknesses.map((w) => (
                  <li key={w} className="text-xs px-2.5 py-1 bg-red-50 text-red-700 rounded-md">{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Suggestions */}
        {analysis.suggestions?.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-amber-600 uppercase mb-2">Gợi ý cải thiện</h4>
            <ul className="space-y-1">
              {analysis.suggestions.map((s, i) => (
                <li key={i} className="text-xs px-2.5 py-1.5 bg-amber-50 text-amber-700 rounded-md">
                  {i + 1}. {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Performance + Similar angles */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Performance Prediction */}
          <div className="p-3 bg-emerald-50/50 rounded-lg space-y-2">
            <h4 className="text-xs font-semibold text-emerald-700 uppercase">Dự đoán hiệu suất</h4>
            <ScoreBar score={analysis.performance_prediction.score} />
            <p className="text-xs text-gray-500">{analysis.performance_prediction.reasoning}</p>
          </div>

          {/* Similar Angle Ideas */}
          {analysis.similar_angle_ideas?.length > 0 && (
            <div className="p-3 bg-indigo-50/50 rounded-lg space-y-2">
              <h4 className="text-xs font-semibold text-indigo-700 uppercase">Ý tưởng angle mới</h4>
              <ul className="text-xs text-gray-600 space-y-1">
                {analysis.similar_angle_ideas.map((idea, i) => (
                  <li key={i}>• {idea}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
