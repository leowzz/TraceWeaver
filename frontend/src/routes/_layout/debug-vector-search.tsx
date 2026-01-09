import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { useMutation } from "@tanstack/react-query"

import { OpenAPI } from "@/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { Loader2, Search } from "lucide-react"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/debug-vector-search")({
  component: DebugVectorSearch,
  head: () => ({
    meta: [
      {
        title: "Debug Vector Search - TraceWeaver",
      },
    ],
  }),
})

interface VectorSearchResult {
  activity_id: number
  activity_title: string
  chunk_text: string
  chunk_index: number
  similarity: number
  metadata: Record<string, unknown>
}

interface VectorSearchResponse {
  success: boolean
  query: string
  results?: VectorSearchResult[] | null
  error?: string | null
  query_embedding_dimensions?: number | null
}

function DebugVectorSearch() {
  const { user } = useAuth()
  const [query, setQuery] = useState("今天做了什么工作")
  const [topK, setTopK] = useState("5")
  const [minSimilarity, setMinSimilarity] = useState("0.7")
  const [result, setResult] = useState<VectorSearchResponse | null>(null)

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
    mutationFn: async (params: { query: string; top_k: number; min_similarity: number }) => {
      const token = typeof OpenAPI.TOKEN === 'function'
        ? await OpenAPI.TOKEN({ method: 'POST', url: '' } as any)
        : OpenAPI.TOKEN

      const response = await fetch(`${OpenAPI.BASE}/api/v1/debug/vector-search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(params),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return response.json() as Promise<VectorSearchResponse>
    },
    onSuccess: (data) => {
      setResult(data)
    },
    onError: (error) => {
      setResult({
        success: false,
        query: query,
        error: error instanceof Error ? error.message : String(error),
      })
    },
  })

  const handleExecute = () => {
    if (query.trim()) {
      executeMutation.mutate({
        query: query,
        top_k: parseInt(topK),
        min_similarity: parseFloat(minSimilarity),
      })
    }
  }

  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 0.9) return "bg-green-500"
    if (similarity >= 0.8) return "bg-green-400"
    if (similarity >= 0.7) return "bg-yellow-500"
    if (similarity >= 0.6) return "bg-orange-500"
    return "bg-red-500"
  }

  return (
    <div className="flex flex-col gap-6 h-full">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Vector Search Debug</h1>
        <p className="text-muted-foreground">
          Semantic search powered by pgvector (Admin only)
        </p>
      </div>

      <div className="flex flex-col gap-4 flex-1 min-h-0">
        {/* Query Input & Config */}
        <Card className="flex-shrink-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Query & Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="query">Query Text</Label>
              <textarea
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full h-24 p-3 text-sm border rounded-md bg-muted/30 resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Enter your search query..."
                spellCheck={false}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="topK">Top K Results</Label>
                <Select value={topK} onValueChange={setTopK}>
                  <SelectTrigger id="topK">
                    <SelectValue placeholder="Select Top K" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="3">3</SelectItem>
                    <SelectItem value="5">5</SelectItem>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="20">20</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="minSimilarity">Min Similarity</Label>
                <Input
                  id="minSimilarity"
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={minSimilarity}
                  onChange={(e) => setMinSimilarity(e.target.value)}
                  placeholder="0.7"
                />
              </div>
            </div>

            <Button
              onClick={handleExecute}
              disabled={executeMutation.isPending || !query.trim()}
              className="w-full"
            >
              {executeMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Search className="mr-2 h-4 w-4" />
              )}
              Execute Search
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
            {result?.results && (
              <CardDescription>
                {result.results.length} result(s) returned
                {result.query_embedding_dimensions && (
                  <span className="ml-2">
                    (Embedding dimensions: {result.query_embedding_dimensions})
                  </span>
                )}
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="flex-1 overflow-auto min-h-0 space-y-4">
            {result ? (
              result.success ? (
                result.results && result.results.length > 0 ? (
                  <div className="space-y-3">
                    {result.results.map((item, idx) => (
                      <Card key={idx} className="border-2">
                        <CardHeader className="pb-2">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="text-xs text-muted-foreground mb-1">
                                #{idx + 1} - Activity #{item.activity_id} - Chunk {item.chunk_index}
                              </div>
                              <CardTitle className="text-sm font-semibold truncate">
                                {item.activity_title}
                              </CardTitle>
                            </div>
                            <div className="flex-shrink-0 text-right">
                              <div className="text-xs text-muted-foreground mb-1">Similarity</div>
                              <div className="text-lg font-bold">
                                {(item.similarity * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <div className="text-xs text-muted-foreground">Score:</div>
                              <Progress 
                                value={item.similarity * 100} 
                                className="flex-1 h-2"
                              />
                            </div>
                          </div>

                          <div>
                            <div className="text-xs text-muted-foreground mb-1">Chunk Text:</div>
                            <div className="text-sm p-2 bg-muted/30 rounded-md whitespace-pre-wrap">
                              {item.chunk_text}
                            </div>
                          </div>

                          {Object.keys(item.metadata).length > 0 && (
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Metadata:</div>
                              <pre className="text-xs font-mono p-2 bg-muted/30 rounded-md overflow-auto">
                                {JSON.stringify(item.metadata, null, 2)}
                              </pre>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-muted-foreground text-sm text-center py-8">
                    No results found. Try adjusting your query or lowering the minimum similarity threshold.
                  </div>
                )
              ) : (
                <div className="p-4 bg-destructive/10 text-destructive rounded-md">
                  <strong>Error:</strong> {result.error}
                </div>
              )
            ) : (
              <div className="text-muted-foreground text-sm text-center py-8">
                Execute a search to see results here.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
