import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { useMutation } from "@tanstack/react-query"

import { OpenAPI } from "@/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, Play } from "lucide-react"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/debug-siyuan-sql")({
  component: DebugSiYuanSQL,
  head: () => ({
    meta: [
      {
        title: "Debug SiYuan SQL - TraceWeaver",
      },
    ],
  }),
})

interface SQLResponse {
  success: boolean
  data?: Record<string, unknown>[] | null
  error?: string | null
}

function DebugSiYuanSQL() {
  const { user } = useAuth()
  const [sql, setSQL] = useState("SELECT * FROM blocks LIMIT 10")
  const [result, setResult] = useState<SQLResponse | null>(null)

  // Check if user is admin
  if (!user?.is_superuser) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Card className="w-[400px]">
          <CardHeader>
            <CardTitle className="text-destructive">Access Denied</CardTitle>
            <CardDescription>
              This page is only accessible to admin users.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  const executeMutation = useMutation({
    mutationFn: async (stmt: string) => {
      const token = typeof OpenAPI.TOKEN === 'function'
        ? await OpenAPI.TOKEN({ method: 'POST', url: '' } as any)
        : OpenAPI.TOKEN

      const response = await fetch(`${OpenAPI.BASE}/api/v1/debug/siyuan-sql`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ stmt }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return response.json() as Promise<SQLResponse>
    },
    onSuccess: (data) => {
      setResult(data)
    },
    onError: (error) => {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : String(error),
      })
    },
  })

  const handleExecute = () => {
    if (sql.trim()) {
      executeMutation.mutate(sql)
    }
  }

  return (
    <div className="flex flex-col gap-6 h-full">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">SiYuan SQL Debug</h1>
        <p className="text-muted-foreground">
          Execute SQL queries against SiYuan database (Admin only)
        </p>
      </div>

      <div className="flex flex-col gap-4 flex-1 min-h-0">
        {/* SQL Editor */}
        <Card className="flex-shrink-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">SQL Statement</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <textarea
              value={sql}
              onChange={(e) => setSQL(e.target.value)}
              className="w-full h-32 p-3 font-mono text-sm border rounded-md bg-muted/30 resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Enter SQL statement..."
              spellCheck={false}
            />
            <Button
              onClick={handleExecute}
              disabled={executeMutation.isPending || !sql.trim()}
            >
              {executeMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Play className="mr-2 h-4 w-4" />
              )}
              Execute
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        <Card className="flex-1 min-h-0 flex flex-col">
          <CardHeader className="pb-2 flex-shrink-0">
            <CardTitle className="text-base flex items-center gap-2">
              Results
              {result && (
                <span className={`text-xs px-2 py-0.5 rounded ${result.success
                  ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                  : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                  }`}>
                  {result.success ? 'Success' : 'Error'}
                </span>
              )}
            </CardTitle>
            {result?.data && (
              <CardDescription>
                {result.data.length} row(s) returned
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="flex-1 overflow-auto min-h-0">
            {result ? (
              result.success ? (
                <pre className="text-xs font-mono bg-muted/30 p-4 rounded-md overflow-auto max-h-full whitespace-pre-wrap">
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              ) : (
                <div className="p-4 bg-destructive/10 text-destructive rounded-md">
                  <strong>Error:</strong> {result.error}
                </div>
              )
            ) : (
              <div className="text-muted-foreground text-sm">
                Execute a query to see results here.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
