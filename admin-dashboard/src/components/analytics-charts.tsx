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
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"


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
    color: "var(--chart-1)",
  },
} satisfies ChartConfig


const severityConfig = {
  count: {
    label: "Assessments",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig


const sourceConfig = {
  count: {
    label: "Assessments",
    color: "var(--chart-3)",
  },
} satisfies ChartConfig


const activityConfig = {
  count: {
    label: "Assessments",
    color: "var(--chart-1)",
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
    <div className="grid gap-6 lg:grid-cols-2">

      {/* Disease Distribution */}

      <Card>

        <CardHeader>

          <CardTitle>
            Disease Distribution
          </CardTitle>

          <CardDescription>
            Number of assessments by predicted condition.
          </CardDescription>

        </CardHeader>

        <CardContent>

          {diseases.length === 0 ? (

            <div className="py-16 text-center text-sm text-muted-foreground">
              No assessment data available.
            </div>

          ) : (

            <ChartContainer
              config={diseaseConfig}
              className="h-[320px] w-full"
            >

              <BarChart
                accessibilityLayer
                data={diseases}
                layout="vertical"
                margin={{
                  left: 15,
                  right: 20,
                }}
              >

                <CartesianGrid
                  horizontal={false}
                />

                <YAxis
                  dataKey="disease"
                  type="category"
                  tickLine={false}
                  axisLine={false}
                  width={140}
                  tick={{
                    fontSize: 11,
                  }}
                />

                <XAxis
                  type="number"
                  allowDecimals={false}
                  tickLine={false}
                  axisLine={false}
                />

                <ChartTooltip
                  cursor={false}
                  content={
                    <ChartTooltipContent />
                  }
                />

                <Bar
                  dataKey="count"
                  fill="var(--color-count)"
                  radius={4}
                />

              </BarChart>

            </ChartContainer>

          )}

        </CardContent>

      </Card>


      {/* Severity Distribution */}

      <Card>

        <CardHeader>

          <CardTitle>
            Severity Distribution
          </CardTitle>

          <CardDescription>
            Frequency of severity levels reported by KILIMO.
          </CardDescription>

        </CardHeader>

        <CardContent>

          {severities.length === 0 ? (

            <div className="py-16 text-center text-sm text-muted-foreground">
              No severity data available.
            </div>

          ) : (

            <ChartContainer
              config={severityConfig}
              className="h-[320px] w-full"
            >

              <BarChart
                accessibilityLayer
                data={severities}
              >

                <CartesianGrid
                  vertical={false}
                />

                <XAxis
                  dataKey="severity"
                  tickLine={false}
                  axisLine={false}
                />

                <YAxis
                  allowDecimals={false}
                  tickLine={false}
                  axisLine={false}
                />

                <ChartTooltip
                  cursor={false}
                  content={
                    <ChartTooltipContent />
                  }
                />

                <Bar
                  dataKey="count"
                  fill="var(--color-count)"
                  radius={6}
                />

              </BarChart>

            </ChartContainer>

          )}

        </CardContent>

      </Card>


      {/* Assessment Activity */}

      <Card className="lg:col-span-2">

        <CardHeader>

          <CardTitle>
            Assessment Activity
          </CardTitle>

          <CardDescription>
            Tomato image assessments completed during
            the last 14 days.
          </CardDescription>

        </CardHeader>

        <CardContent>

          <ChartContainer
            config={activityConfig}
            className="h-[300px] w-full"
          >

            <AreaChart
              accessibilityLayer
              data={activity}
              margin={{
                left: 5,
                right: 15,
              }}
            >

              <CartesianGrid
                vertical={false}
              />

              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tickFormatter={shortDate}
              />

              <YAxis
                allowDecimals={false}
                tickLine={false}
                axisLine={false}
              />

              <ChartTooltip
                content={
                  <ChartTooltipContent
                    labelFormatter={
                      (value) =>
                        shortDate(
                          String(value)
                        )
                    }
                  />
                }
              />

              <Area
                dataKey="count"
                type="monotone"
                fill="var(--color-count)"
                fillOpacity={0.2}
                stroke="var(--color-count)"
              />

            </AreaChart>

          </ChartContainer>

        </CardContent>

      </Card>


      {/* Sources */}

      <Card className="lg:col-span-2">

        <CardHeader>

          <CardTitle>
            Assessment Sources
          </CardTitle>

          <CardDescription>
            How tomato images entered the KILIMO system.
          </CardDescription>

        </CardHeader>

        <CardContent>

          {sources.length === 0 ? (

            <div className="py-16 text-center text-sm text-muted-foreground">
              No source information available.
            </div>

          ) : (

            <ChartContainer
              config={sourceConfig}
              className="h-[260px] w-full"
            >

              <BarChart
                accessibilityLayer
                data={sources}
              >

                <CartesianGrid
                  vertical={false}
                />

                <XAxis
                  dataKey="source"
                  tickLine={false}
                  axisLine={false}
                />

                <YAxis
                  allowDecimals={false}
                  tickLine={false}
                  axisLine={false}
                />

                <ChartTooltip
                  content={
                    <ChartTooltipContent />
                  }
                />

                <Bar
                  dataKey="count"
                  fill="var(--color-count)"
                  radius={6}
                />

              </BarChart>

            </ChartContainer>

          )}

        </CardContent>

      </Card>

    </div>
  )
}