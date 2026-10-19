"use client"

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts"

import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"

import {
  BarChart3,
  ChartNoAxesCombined,
  Layers3,
  Radar,
} from "lucide-react"


interface DiseaseData {
  disease: string
  count: number
}

interface SeverityData {
  severity: string
  count: number
}

interface SourceData {
  source: string
  count: number
}

interface ActivityData {
  date: string
  count: number
}


interface AnalyticsChartsProps {
  diseases: DiseaseData[]
  severities: SeverityData[]
  sources: SourceData[]
  activity: ActivityData[]
}


const diseaseConfig = {
  count: {
    label: "Assessments",
    color:
      "var(--chart-1)",
  },
} satisfies ChartConfig


const severityConfig = {
  count: {
    label: "Assessments",
    color:
      "var(--chart-3)",
  },
} satisfies ChartConfig


const sourceConfig = {
  count: {
    label: "Assessments",
    color:
      "var(--chart-2)",
  },
} satisfies ChartConfig


const activityConfig = {
  count: {
    label: "Assessments",
    color:
      "var(--chart-1)",
  },
} satisfies ChartConfig


function shortDate(
  value: string
) {
  return new Intl.DateTimeFormat(
    "en-KE",
    {
      month: "short",
      day: "numeric",
    }
  ).format(
    new Date(
      `${value}T12:00:00`
    )
  )
}


export function AnalyticsCharts({
  diseases,
  severities,
  sources,
  activity,
}: AnalyticsChartsProps) {
  return (
    <div className="grid gap-6">

      {/* Activity */}

      <ChartPanel
        title="Assessment activity"
        description="Completed tomato image assessments over the selected period."
        icon={ChartNoAxesCombined}
      >

        {activity.length === 0 ? (

          <EmptyState
            text="No assessment activity is available for this period."
          />

        ) : (

          <ChartContainer
            config={activityConfig}
            className="h-[320px] w-full"
          >

            <AreaChart
              accessibilityLayer
              data={activity}
              margin={{
                left: 4,
                right: 12,
                top: 12,
              }}
            >

              <CartesianGrid
                vertical={false}
                strokeDasharray="3 3"
              />

              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={10}
                tickFormatter={shortDate}
                minTickGap={24}
                fontSize={11}
              />

              <YAxis
                allowDecimals={false}
                tickLine={false}
                axisLine={false}
                width={32}
                fontSize={11}
              />

              <ChartTooltip
                cursor={{
                  stroke:
                    "var(--border)",
                  strokeDasharray:
                    "4 4",
                }}
                content={
                  <ChartTooltipContent
                    labelFormatter={
                      (value) =>
                        shortDate(
                          String(
                            value
                          )
                        )
                    }
                  />
                }
              />

              <Area
                dataKey="count"
                type="monotone"
                stroke="var(--color-count)"
                strokeWidth={2}
                fill="var(--color-count)"
                fillOpacity={0.12}
                dot={false}
                activeDot={{
                  r: 4,
                }}
              />

            </AreaChart>

          </ChartContainer>

        )}

      </ChartPanel>


      {/* Secondary charts */}

      <div className="grid gap-6 xl:grid-cols-2">

        <ChartPanel
          title="Disease distribution"
          description="Assessment frequency by predicted tomato condition."
          icon={BarChart3}
        >

          {diseases.length === 0 ? (

            <EmptyState
              text="No disease distribution data is available."
            />

          ) : (

            <ChartContainer
              config={diseaseConfig}
              className="h-[390px] w-full"
            >

              <BarChart
                accessibilityLayer
                data={diseases}
                layout="vertical"
                margin={{
                  left: 10,
                  right: 18,
                }}
              >

                <CartesianGrid
                  horizontal={false}
                  strokeDasharray="3 3"
                />

                <YAxis
                  dataKey="disease"
                  type="category"
                  tickLine={false}
                  axisLine={false}
                  width={150}
                  fontSize={10}
                />

                <XAxis
                  type="number"
                  allowDecimals={false}
                  tickLine={false}
                  axisLine={false}
                  fontSize={11}
                />

                <ChartTooltip
                  cursor={{
                    fill:
                      "var(--muted)",
                    opacity: 0.35,
                  }}
                  content={
                    <ChartTooltipContent />
                  }
                />

                <Bar
                  dataKey="count"
                  fill="var(--color-count)"
                  radius={[
                    0,
                    5,
                    5,
                    0,
                  ]}
                  maxBarSize={18}
                />

              </BarChart>

            </ChartContainer>

          )}

        </ChartPanel>


        <ChartPanel
          title="Severity distribution"
          description="Frequency of severity levels assigned by the image-analysis pipeline."
          icon={Radar}
        >

          {severities.length === 0 ? (

            <EmptyState
              text="No severity information is available."
            />

          ) : (

            <ChartContainer
              config={severityConfig}
              className="h-[390px] w-full"
            >

              <BarChart
                accessibilityLayer
                data={severities}
                margin={{
                  top: 20,
                  left: 4,
                  right: 12,
                }}
              >

                <CartesianGrid
                  vertical={false}
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="severity"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={10}
                  fontSize={11}
                />

                <YAxis
                  allowDecimals={false}
                  tickLine={false}
                  axisLine={false}
                  width={32}
                  fontSize={11}
                />

                <ChartTooltip
                  cursor={{
                    fill:
                      "var(--muted)",
                    opacity: 0.35,
                  }}
                  content={
                    <ChartTooltipContent />
                  }
                />

                <Bar
                  dataKey="count"
                  fill="var(--color-count)"
                  radius={[
                    5,
                    5,
                    0,
                    0,
                  ]}
                  maxBarSize={54}
                />

              </BarChart>

            </ChartContainer>

          )}

        </ChartPanel>

      </div>


      {/* Sources */}

      <ChartPanel
        title="Assessment sources"
        description="Channels through which tomato images entered the KILIMO assessment pipeline."
        icon={Layers3}
      >

        {sources.length === 0 ? (

          <EmptyState
            text="No source information is available."
          />

        ) : (

          <ChartContainer
            config={sourceConfig}
            className="h-[260px] w-full"
          >

            <BarChart
              accessibilityLayer
              data={sources}
              margin={{
                top: 16,
                left: 4,
                right: 12,
              }}
            >

              <CartesianGrid
                vertical={false}
                strokeDasharray="3 3"
              />

              <XAxis
                dataKey="source"
                tickLine={false}
                axisLine={false}
                tickMargin={10}
                fontSize={11}
              />

              <YAxis
                allowDecimals={false}
                tickLine={false}
                axisLine={false}
                width={32}
                fontSize={11}
              />

              <ChartTooltip
                cursor={{
                  fill:
                    "var(--muted)",
                  opacity: 0.35,
                }}
                content={
                  <ChartTooltipContent />
                }
              />

              <Bar
                dataKey="count"
                fill="var(--color-count)"
                radius={[
                  5,
                  5,
                  0,
                  0,
                ]}
                maxBarSize={70}
              />

            </BarChart>

          </ChartContainer>

        )}

      </ChartPanel>

    </div>
  )
}


function ChartPanel({
  title,
  description,
  icon: Icon,
  children,
}: {
  title: string
  description: string
  icon: React.ComponentType<{
    className?: string
  }>
  children: React.ReactNode
}) {
  return (
    <section className="overflow-hidden rounded-xl border bg-card">

      <div className="flex items-start gap-3 border-b px-5 py-4">

        <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border bg-muted/40">

          <Icon className="size-3.5" />

        </div>


        <div>

          <h2 className="text-sm font-semibold">
            {title}
          </h2>

          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            {description}
          </p>

        </div>

      </div>


      <div className="p-5">

        {children}

      </div>

    </section>
  )
}


function EmptyState({
  text,
}: {
  text: string
}) {
  return (
    <div className="flex min-h-52 items-center justify-center">

      <p className="text-sm text-muted-foreground">
        {text}
      </p>

    </div>
  )
}