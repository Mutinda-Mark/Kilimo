export interface LatestAssessment {
  id: number
  phone_number: string | null
  disease: string
  confidence: number
  severity: string
  affected_area_percentage: number
  source: string
  created_at: string
}

export interface DashboardSummary {
  total_sessions: number
  total_messages: number
  total_assessments: number
  active_sessions_24h: number
  average_confidence: number | null
  latest_assessment: LatestAssessment | null
}

export interface Assessment {
  id: number
  phone_number: string | null
  disease: string
  confidence: number
  severity: string
  affected_area_percentage: number
  label_index: number | null
  all_scores: Record<string, number>
  source: string
  created_at: string
}

export interface AssessmentResponse {
  count: number
  limit: number
  offset: number
  assessments: Assessment[]
}

export interface DiseaseStatistic {
  disease: string
  count: number
  average_confidence: number | null
  average_affected_area: number | null
}

export interface DiseaseResponse {
  count: number
  diseases: DiseaseStatistic[]
}

export interface FarmerSession {
  phone_number: string
  language: string
  last_disease: string | null
  last_severity: string | null
  last_confidence: number | null
  last_active_at: string
}

export interface SessionResponse {
  count: number
  limit: number
  offset: number
  sessions: FarmerSession[]
}

export interface ConversationMessage {
  id: number
  phone_number: string
  role: "farmer" | "system"
  message_type: "text" | "image"
  content: string | null
  created_at: string
}

export interface ConversationHistoryResponse {
  phone_number: string
  count: number
  history: ConversationMessage[]
}

export interface SeverityStatistic {
  severity: string
  count: number
}

export interface SeverityResponse {
  count: number
  severities: SeverityStatistic[]
}

export interface SourceStatistic {
  source: string
  count: number
}

export interface SourceResponse {
  count: number
  sources: SourceStatistic[]
}

export interface ActivityPoint {
  date: string
  count: number
}

export interface ActivityResponse {
  days: number
  activity: ActivityPoint[]
}

export async function getSeverityStatistics() {
  return adminFetch<SeverityResponse>(
    "/admin/analytics/severity"
  )
}


export async function getSourceStatistics() {
  return adminFetch<SourceResponse>(
    "/admin/analytics/sources"
  )
}


export async function getAssessmentActivity(
  days = 14
) {
  return adminFetch<ActivityResponse>(
    `/admin/analytics/activity?days=${days}`
  )
}

export interface DatabaseStatistics {
  connected: boolean
  sessions: number
  conversation_messages: number
  assessments: number
  whatsapp_messages: number
}

export interface WhatsAppStatistics {
  total: number
  processing: number
  completed: number
  failed: number
  received_24h: number
}

export interface WhatsAppProcessingMessage {
  message_id: string
  phone_number: string | null
  message_type: string | null
  status: string
  error_message: string | null
  received_at: string
  completed_at: string | null
  updated_at: string
}

export interface WhatsAppProcessingResponse {
  count: number
  messages: WhatsAppProcessingMessage[]
}

export interface ModelInformation {
  backbone: string
  num_classes: number
  image_size: number
  task: string
  status: string
}

export async function getDatabaseStatistics() {
  return adminFetch<DatabaseStatistics>(
    "/admin/system/database"
  )
}


export async function getWhatsAppStatistics() {
  return adminFetch<WhatsAppStatistics>(
    "/admin/system/whatsapp"
  )
}


export async function getRecentWhatsAppMessages(
  limit = 20
) {
  return adminFetch<WhatsAppProcessingResponse>(
    `/admin/system/whatsapp/recent?limit=${limit}`
  )
}


export async function getModelInformation() {
  return adminFetch<ModelInformation>(
    "/admin/system/model"
  )
}

function getConfiguration() {
  const apiUrl = process.env.KILIMO_API_URL
  const token = process.env.KILIMO_ADMIN_TOKEN

  if (!apiUrl) {
    throw new Error(
      "KILIMO_API_URL is not configured."
    )
  }

  if (!token) {
    throw new Error(
      "KILIMO_ADMIN_TOKEN is not configured."
    )
  }

  return {
    apiUrl,
    token,
  }
}


async function adminFetch<T>(
  path: string
): Promise<T> {
  const { apiUrl, token } = getConfiguration()

  const response = await fetch(
    `${apiUrl}${path}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
      },

      cache: "no-store",
    }
  )

  if (!response.ok) {
    const body = await response.text()

    throw new Error(
      `KILIMO API request failed (${response.status}): ${body}`
    )
  }

  return response.json() as Promise<T>
}


export async function getDashboardSummary() {
  return adminFetch<DashboardSummary>(
    "/admin/summary"
  )
}


export async function getRecentAssessments(
  limit = 10,
  offset = 0
) {
  return adminFetch<AssessmentResponse>(
    `/admin/assessments?limit=${limit}&offset=${offset}`
  )
}


export async function getDiseaseStatistics() {
  return adminFetch<DiseaseResponse>(
    "/admin/diseases"
  )
}


export async function getFarmerSessions(
  limit = 50,
  offset = 0
) {
  return adminFetch<SessionResponse>(
    `/admin/sessions?limit=${limit}&offset=${offset}`
  )
}


export async function getFarmerHistory(
  phoneNumber: string,
  limit = 100
) {
  return adminFetch<ConversationHistoryResponse>(
    `/admin/sessions/${encodeURIComponent(
      phoneNumber
    )}/history?limit=${limit}`
  )
}

export async function getAssessment(
  assessmentId: number
) {
  return adminFetch<Assessment>(
    `/admin/assessments/${assessmentId}`
  )
}