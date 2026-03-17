export interface UserUsage {
  searches: { used: number; limit: number }
  ai_credits: { used: number; limit: number }
  boards: { limit: number }
  saved_ads: { limit: number }
}

export interface UserProfile {
  id: string
  email: string
  full_name: string
  tier: string
  subscription_status: string | null
  usage: UserUsage
  email_alerts_enabled: boolean
  daily_digest_enabled: boolean
  telegram_connected: boolean
  telegram_enabled: boolean
  stripe_publishable_key: string
}
