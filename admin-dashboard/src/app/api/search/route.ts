import {
  NextResponse,
} from "next/server"

import {
  requireAdminUser,
} from "@/lib/auth"

import {
  getFarmerSessions,
  getRecentAssessments,
} from "@/lib/kilimo-api"


export async function GET(
  request: Request
) {
  await requireAdminUser()

  const {
    searchParams,
  } =
    new URL(request.url)

  const query =
    searchParams
      .get("q")
      ?.trim()
      .toLowerCase() ??
    ""


  if (
    query.length < 2
  ) {
    return NextResponse.json({
      farmers: [],
      assessments: [],
    })
  }


  const [
    farmerData,
    assessmentData,
  ] =
    await Promise.all([
      getFarmerSessions(
        100,
        0
      ),

      getRecentAssessments(
        100,
        0
      ),
    ])


  const farmers =
    farmerData.sessions
      .filter(
        (farmer) =>
          farmer.phone_number
            .toLowerCase()
            .includes(query) ||
          farmer.last_disease
            ?.toLowerCase()
            .includes(query)
      )
      .slice(
        0,
        5
      )


  const assessments =
    assessmentData.assessments
      .filter(
        (assessment) =>
          assessment.disease
            .toLowerCase()
            .includes(query) ||
          assessment.phone_number
            ?.toLowerCase()
            .includes(query) ||
          String(
            assessment.id
          ).includes(
            query
          )
      )
      .slice(
        0,
        5
      )


  return NextResponse.json({
    farmers,
    assessments,
  })
}