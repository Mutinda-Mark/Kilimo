"use client"

import {
  FileSearch,
  Leaf,
  LoaderCircle,
  Search,
  UserRound,
  X,
} from "lucide-react"

import {
  useEffect,
  useRef,
  useState,
} from "react"

import {
  useRouter,
} from "next/navigation"


interface FarmerResult {
  phone_number: string
  last_disease: string | null
}


interface AssessmentResult {
  id: number
  disease: string
  confidence: number
}


interface SearchResults {
  farmers: FarmerResult[]
  assessments: AssessmentResult[]
}


const EMPTY_RESULTS: SearchResults = {
  farmers: [],
  assessments: [],
}


function maskPhoneNumber(
  phoneNumber: string
) {
  if (phoneNumber.length < 8) {
    return phoneNumber
  }

  return (
    `${phoneNumber.slice(0, 6)}••••${phoneNumber.slice(-3)}`
  )
}


function percentage(
  value: number
) {
  return `${(value * 100).toFixed(1)}%`
}


export function GlobalSearch() {
  const router =
    useRouter()

  const inputRef =
    useRef<HTMLInputElement>(
      null
    )

  const [
    open,
    setOpen,
  ] =
    useState(false)

  const [
    query,
    setQuery,
  ] =
    useState("")

  const [
    loading,
    setLoading,
  ] =
    useState(false)

  const [
    results,
    setResults,
  ] =
    useState<SearchResults>(
      EMPTY_RESULTS
    )


  const normalizedQuery =
    query.trim()

  const hasSearchQuery =
    normalizedQuery.length >= 2


  /*
   * Global keyboard shortcuts.
   *
   * Ctrl + K / Cmd + K:
   * Opens search.
   *
   * Escape:
   * Closes search.
   */
  useEffect(() => {
    function shortcut(
      event: KeyboardEvent
    ) {
      const isSearchShortcut =
        event.key.toLowerCase() ===
          "k" &&
        (
          event.ctrlKey ||
          event.metaKey
        )

      if (
        isSearchShortcut
      ) {
        event.preventDefault()

        setOpen(true)
      }


      if (
        event.key ===
        "Escape"
      ) {
        setOpen(false)
      }
    }


    window.addEventListener(
      "keydown",
      shortcut
    )


    return () => {
      window.removeEventListener(
        "keydown",
        shortcut
      )
    }
  }, [])


  /*
   * Focus the input whenever the
   * command palette is opened.
   */
  useEffect(() => {
    if (!open) {
      return
    }

    const frame =
      window.requestAnimationFrame(
        () => {
          inputRef.current
            ?.focus()
        }
      )


    return () => {
      window.cancelAnimationFrame(
        frame
      )
    }
  }, [open])


  /*
   * Debounced search.
   *
   * We deliberately do not call
   * setResults synchronously when
   * the query is shorter than two
   * characters. This keeps React's
   * set-state-in-effect lint rule happy.
   */
  useEffect(() => {
    if (
      normalizedQuery.length < 2
    ) {
      return
    }


    const controller =
      new AbortController()


    const timeout =
      window.setTimeout(
        async () => {
          setLoading(true)

          try {
            const response =
              await fetch(
                `/api/search?q=${
                  encodeURIComponent(
                    normalizedQuery
                  )
                }`,
                {
                  signal:
                    controller.signal,
                  cache:
                    "no-store",
                }
              )


            if (!response.ok) {
              throw new Error(
                `Search request failed with status ${response.status}`
              )
            }


            const data =
              await response.json() as SearchResults


            if (
              !controller.signal.aborted
            ) {
              setResults(data)
            }

          } catch (error) {
            if (
              error instanceof DOMException &&
              error.name ===
                "AbortError"
            ) {
              return
            }


            console.error(
              "Global search failed:",
              error
            )


            if (
              !controller.signal.aborted
            ) {
              setResults(
                EMPTY_RESULTS
              )
            }

          } finally {
            if (
              !controller.signal.aborted
            ) {
              setLoading(false)
            }
          }
        },
        250
      )


    return () => {
      window.clearTimeout(
        timeout
      )

      controller.abort()
    }

  }, [normalizedQuery])


  function closeSearch() {
    setOpen(false)
    setQuery("")
    setResults(
      EMPTY_RESULTS
    )
  }


  function navigate(
    path: string
  ) {
    closeSearch()

    router.push(path)
  }


  const showNoResults =
    hasSearchQuery &&
    !loading &&
    results.farmers.length === 0 &&
    results.assessments.length === 0


  return (
    <>

      {/* Desktop search trigger */}

      <button
        type="button"
        onClick={() =>
          setOpen(true)
        }
        className="hidden h-9 min-w-64 items-center gap-2 rounded-lg border bg-background px-3 text-left text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring lg:flex"
      >

        <Search className="size-4" />

        <span className="flex-1">
          Search KILIMO
        </span>

        <kbd className="rounded border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
          Ctrl K
        </kbd>

      </button>


      {/* Search overlay */}

      {open && (

        <div
          className="fixed inset-0 z-[100] flex items-start justify-center bg-black/40 px-4 pt-[12vh] backdrop-blur-sm"
          onMouseDown={
            (event) => {
              if (
                event.target ===
                event.currentTarget
              ) {
                closeSearch()
              }
            }
          }
        >

          <div
            role="dialog"
            aria-modal="true"
            aria-label="Search KILIMO"
            className="w-full max-w-2xl overflow-hidden rounded-xl border bg-popover shadow-2xl"
          >

            {/* Search input */}

            <div className="flex items-center border-b px-4">

              <Search className="size-4 shrink-0 text-muted-foreground" />


              <input
                ref={inputRef}
                value={query}
                onChange={
                  (event) =>
                    setQuery(
                      event.target.value
                    )
                }
                placeholder="Search farmers, diseases or assessment IDs..."
                aria-label="Search KILIMO"
                className="h-14 min-w-0 flex-1 bg-transparent px-3 text-sm outline-none placeholder:text-muted-foreground"
              />


              {loading ? (

                <LoaderCircle className="size-4 shrink-0 animate-spin text-muted-foreground" />

              ) : (

                <button
                  type="button"
                  aria-label="Close search"
                  title="Close"
                  onClick={
                    closeSearch
                  }
                  className="flex size-8 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                >
                  <X className="size-4" />
                </button>

              )}

            </div>


            {/* Results */}

            <div className="max-h-[430px] overflow-y-auto p-2">

              {!hasSearchQuery ? (

                <div className="px-4 py-12 text-center">

                  <div className="mx-auto flex size-10 items-center justify-center rounded-lg border bg-muted/40">
                    <FileSearch className="size-4 text-muted-foreground" />
                  </div>

                  <p className="mt-3 text-sm font-medium">
                    Search KILIMO
                  </p>

                  <p className="mt-1 text-xs text-muted-foreground">
                    Enter at least two characters to search farmers and assessments.
                  </p>

                </div>

              ) : (

                <>

                  {/* Farmers */}

                  {results.farmers.length >
                    0 && (

                    <section className="mb-3">

                      <p className="px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                        Farmers
                      </p>


                      <div className="space-y-1">

                        {results.farmers.map(
                          (farmer) => (

                            <button
                              key={
                                farmer.phone_number
                              }
                              type="button"
                              onClick={() =>
                                navigate(
                                  `/farmers/${
                                    encodeURIComponent(
                                      farmer.phone_number
                                    )
                                  }`
                                )
                              }
                              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            >

                              <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border bg-muted/40">
                                <UserRound className="size-3.5" />
                              </div>


                              <div className="min-w-0 flex-1">

                                <p className="truncate font-mono text-xs font-medium">
                                  {maskPhoneNumber(
                                    farmer.phone_number
                                  )}
                                </p>

                                <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                                  {farmer.last_disease ??
                                    "No assessment"}
                                </p>

                              </div>


                              <span className="text-[10px] text-muted-foreground">
                                Farmer
                              </span>

                            </button>

                          )
                        )}

                      </div>

                    </section>

                  )}


                  {/* Assessments */}

                  {results.assessments.length >
                    0 && (

                    <section>

                      <p className="px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                        Assessments
                      </p>


                      <div className="space-y-1">

                        {results.assessments.map(
                          (
                            assessment
                          ) => (

                          <button
                            key={
                              assessment.id
                            }
                            type="button"
                            onClick={() =>
                              navigate(
                                `/assessments/${assessment.id}`
                              )
                            }
                            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          >

                            <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border bg-muted/40">
                              <Leaf className="size-3.5" />
                            </div>


                            <div className="min-w-0 flex-1">

                              <p className="truncate text-xs font-medium">
                                {assessment.disease}
                              </p>

                              <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                                Assessment A-
                                {assessment.id}
                              </p>

                            </div>


                            <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                              {percentage(
                                assessment.confidence
                              )}
                            </span>

                          </button>

                          )
                        )}

                      </div>

                    </section>

                  )}


                  {/* Loading state */}

                  {loading &&
                    results.farmers.length ===
                      0 &&
                    results.assessments.length ===
                      0 && (

                    <div className="px-4 py-12 text-center">

                      <LoaderCircle className="mx-auto size-5 animate-spin text-muted-foreground" />

                      <p className="mt-3 text-xs text-muted-foreground">
                        Searching KILIMO...
                      </p>

                    </div>

                  )}


                  {/* Empty results */}

                  {showNoResults && (

                    <div className="px-4 py-12 text-center">

                      <div className="mx-auto flex size-10 items-center justify-center rounded-lg border bg-muted/40">
                        <FileSearch className="size-4 text-muted-foreground" />
                      </div>

                      <p className="mt-3 text-sm font-medium">
                        No results found
                      </p>

                      <p className="mt-1 text-xs text-muted-foreground">
                        No farmers or assessments match &quot;{normalizedQuery}&quot;.
                      </p>

                    </div>

                  )}

                </>

              )}

            </div>


            {/* Footer */}

            <div className="flex items-center justify-between border-t bg-muted/20 px-4 py-2">

              <p className="text-[10px] text-muted-foreground">
                Search farmer sessions and CV assessments
              </p>


              <div className="flex items-center gap-2">

                <kbd className="rounded border bg-background px-1.5 py-0.5 font-mono text-[9px] text-muted-foreground">
                  ESC
                </kbd>

                <span className="text-[10px] text-muted-foreground">
                  Close
                </span>

              </div>

            </div>

          </div>

        </div>

      )}

    </>
  )
}