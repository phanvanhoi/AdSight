import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bell, Check } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { getUnreadCount, listNotifications, markRead, markAllRead } from '../../api/alerts'
import type { NotificationItem } from '../../api/alerts'

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Vừa xong'
  if (mins < 60) return `${mins} phút trước`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} giờ trước`
  const days = Math.floor(hours / 24)
  return `${days} ngày trước`
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: unread } = useQuery({
    queryKey: ['unread-count'],
    queryFn: getUnreadCount,
    refetchInterval: 60000,
  })

  const { data: notifData } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => listNotifications(1),
    enabled: open,
  })

  const markReadMut = useMutation({
    mutationFn: markRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unread-count'] })
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const markAllMut = useMutation({
    mutationFn: markAllRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unread-count'] })
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleNotifClick = (notif: NotificationItem) => {
    if (!notif.is_read) {
      markReadMut.mutate(notif.id)
    }
    // Navigate to first ad if available
    const adIds = (notif.data as Record<string, unknown>)?.ad_ids as string[] | undefined
    if (adIds && adIds.length > 0) {
      navigate(`/ads/${adIds[0]}`)
      setOpen(false)
    }
  }

  const count = unread?.count || 0

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
      >
        <Bell size={18} />
        {count > 0 && (
          <span className="absolute top-1 right-1 min-w-[16px] h-4 px-1 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
            {count > 99 ? '99+' : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl border border-gray-200 shadow-lg z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <h3 className="text-sm font-semibold text-gray-900">Thông báo</h3>
            {count > 0 && (
              <button
                onClick={() => markAllMut.mutate()}
                className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 font-medium"
              >
                <Check size={12} />
                Đọc tất cả
              </button>
            )}
          </div>

          {/* Notifications list */}
          <div className="max-h-96 overflow-y-auto">
            {notifData?.results && notifData.results.length > 0 ? (
              notifData.results.map((notif) => (
                <button
                  key={notif.id}
                  onClick={() => handleNotifClick(notif)}
                  className={`w-full text-left px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors ${
                    !notif.is_read ? 'bg-primary-50/50' : ''
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {!notif.is_read && (
                      <span className="mt-1.5 w-2 h-2 bg-primary-500 rounded-full flex-shrink-0" />
                    )}
                    <div className={!notif.is_read ? '' : 'ml-4'}>
                      <p className={`text-sm ${!notif.is_read ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>
                        {notif.title}
                      </p>
                      {notif.body && (
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{notif.body}</p>
                      )}
                      <p className="text-xs text-gray-400 mt-1">{timeAgo(notif.created_at)}</p>
                    </div>
                  </div>
                </button>
              ))
            ) : (
              <div className="py-8 text-center text-sm text-gray-400">
                Chưa có thông báo
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
