export default function DashboardLoading() {
  return (
    <main className="min-h-screen">

      <div className="mx-auto w-full max-w-[1600px] px-6 py-8 lg:px-8 xl:px-10">

        <div className="space-y-3">

          <div className="h-3 w-36 animate-pulse rounded bg-muted" />

          <div className="h-8 w-52 animate-pulse rounded-lg bg-muted" />

          <div className="h-4 w-96 max-w-full animate-pulse rounded bg-muted" />

        </div>


        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">

          {Array.from({
            length: 4,
          }).map(
            (_, index) => (

              <div
                key={index}
                className="h-28 animate-pulse rounded-xl border bg-card"
              />

            )
          )}

        </div>


        <div className="mt-6 grid gap-6 xl:grid-cols-2">

          <div className="h-[380px] animate-pulse rounded-xl border bg-card" />

          <div className="h-[380px] animate-pulse rounded-xl border bg-card" />

        </div>

      </div>

    </main>
  )
}