import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense, useState } from "react"

import type { ImageAnalysisPublic } from "@/client"
import { ImageAnalysesService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import { getColumns } from "@/components/ImageAnalyses/columns"
import { ImageAnalysisDetail } from "@/components/ImageAnalyses/ImageAnalysisDetail"
import PendingItems from "@/components/Pending/PendingItems"

function getImageAnalysesQueryOptions(page: number, pageSize: number = 100) {
    return {
        queryFn: () =>
            ImageAnalysesService.readImageAnalyses({
                skip: (page - 1) * pageSize,
                limit: pageSize,
                status: 'COMPLETED',
            }),
        queryKey: ["image-analyses", "COMPLETED", page, pageSize],
    }
}

export const Route = createFileRoute("/_layout/image-analyses")({
    component: ImageAnalyses,
    head: () => ({
        meta: [
            {
                title: "Image Analyses - TraceWeaver",
            },
        ],
    }),
})

function ImageAnalysesContent() {
    const page = 1 // TODO: Pagination state if needed
    const pageSize = 100
    const { data: analyses } = useSuspenseQuery(getImageAnalysesQueryOptions(page, pageSize))

    const [selectedAnalysis, setSelectedAnalysis] = useState<ImageAnalysisPublic | null>(null)
    const [detailOpen, setDetailOpen] = useState(false)

    const handleViewDetail = (analysis: ImageAnalysisPublic) => {
        setSelectedAnalysis(analysis)
        setDetailOpen(true)
    }

    const handleNavigate = (direction: 'next' | 'prev') => {
        if (!selectedAnalysis || !analyses?.data) return

        const currentIndex = analyses.data.findIndex(a => a.id === selectedAnalysis.id)
        if (currentIndex === -1) return

        // All items are COMPLETED now due to backend filtering
        const nextIndex = direction === 'next' ? currentIndex + 1 : currentIndex - 1

        // Boundary checks
        if (nextIndex >= 0 && nextIndex < analyses.data.length) {
            setSelectedAnalysis(analyses.data[nextIndex])
        }
    }

    return (
        <>
            <DataTable
                columns={getColumns({ onViewDetail: handleViewDetail }) as any}
                data={analyses.data}
            />

            <ImageAnalysisDetail
                analysis={selectedAnalysis}
                open={detailOpen}
                onOpenChange={setDetailOpen}
                onNext={() => handleNavigate('next')}
                onPrev={() => handleNavigate('prev')}
            />
        </>
    )
}

function ImageAnalyses() {
    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Image Analyses</h1>
                    <p className="text-muted-foreground">
                        View results of LLM image analysis tasks
                    </p>
                </div>
            </div>

            <Suspense fallback={<PendingItems />}>
                <ImageAnalysesContent />
            </Suspense>
        </div>
    )
}
