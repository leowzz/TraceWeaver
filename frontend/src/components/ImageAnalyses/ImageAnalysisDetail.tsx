import type { ImageAnalysisPublic } from "@/client"
import { OpenAPI } from "@/client"
import { useQuery } from "@tanstack/react-query"
import { format } from "date-fns"
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"

interface ImageAnalysisDetailProps {
    analysis: ImageAnalysisPublic | null
    open: boolean
    onOpenChange: (open: boolean) => void
    onNext?: () => void
    onPrev?: () => void
}

export function ImageAnalysisDetail({
    analysis,
    open,
    onOpenChange,
    onNext,
    onPrev,
}: ImageAnalysisDetailProps) {
    if (!analysis) return null

    // Query to fetch image blob URL
    const { data: imageUrl, isLoading: isImageLoading } = useQuery({
        queryKey: ["image-analysis-image", analysis.id],
        queryFn: async () => {
            // Bypass generated client to force Blob response
            const token = typeof OpenAPI.TOKEN === 'function'
                ? await OpenAPI.TOKEN({ method: 'GET', url: '' } as any)
                : OpenAPI.TOKEN;

            const headers: HeadersInit = {}
            if (token) {
                headers['Authorization'] = `Bearer ${token}`
            }

            const response = await fetch(`${OpenAPI.BASE}/api/v1/image-analyses/${analysis.id}/image`, {
                method: 'GET',
                headers,
            })

            if (!response.ok) {
                throw new Error('Failed to fetch image')
            }

            const blob = await response.blob()
            return URL.createObjectURL(blob)
        },
        enabled: open && !!analysis,
        // Cache time for image URL
        staleTime: 1000 * 60 * 5,
    })

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            {/* Use !max-w to override dialog default sm:max-w-lg */}
            <DialogContent className="!max-w-[90vw] w-[1600px] !h-[85vh] flex flex-col p-6">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        Image Analysis Detail #{analysis.id}
                        <Badge
                            variant={
                                analysis.status === "COMPLETED"
                                    ? "default"
                                    : analysis.status === "FAILED"
                                        ? "destructive"
                                        : "secondary"
                            }
                        >
                            {analysis.status}
                        </Badge>
                    </DialogTitle>
                    <DialogDescription>
                        Analyzed by {analysis.model_name} on{" "}
                        {format(new Date(analysis.created_at), "PPpp")}
                    </DialogDescription>
                </DialogHeader>

                <div className="flex flex-1 gap-6 overflow-hidden min-h-0">
                    {/* Image Section - Larger area */}
                    <div className="w-[70%] flex items-center justify-center bg-muted/20 rounded-lg overflow-hidden relative border">
                        {isImageLoading ? (
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        ) : imageUrl ? (
                            <img
                                src={imageUrl}
                                alt={analysis.img_path}
                                className="max-w-full max-h-full object-contain"
                            />
                        ) : (
                            <div className="text-muted-foreground">Failed to load image</div>
                        )}
                    </div>

                    {/* Content Section */}
                    <div className="w-[30%] flex flex-col gap-4">
                        <div>
                            <h4 className="font-semibold mb-2">Image Path</h4>
                            <code className="text-sm bg-muted px-2 py-1 rounded block break-all">
                                {analysis.img_path}
                            </code>
                        </div>

                        {analysis.error_message && (
                            <div className="text-destructive">
                                <h4 className="font-semibold mb-2">Error</h4>
                                <p className="text-sm">{analysis.error_message}</p>
                            </div>
                        )}

                        <div className="flex-1 min-h-0 flex flex-col">
                            <h4 className="font-semibold mb-2">Analysis Result</h4>
                            <div className="flex-1 border rounded-md p-4 overflow-auto bg-muted/10">
                                <div className="whitespace-pre-wrap text-sm font-mono">
                                    {analysis.analysis_result || "No result content"}
                                </div>
                            </div>
                        </div>

                        {/* Navigation Buttons */}
                        <div className="flex justify-between pt-2">
                            <Button
                                variant="outline"
                                onClick={onPrev}
                                disabled={!onPrev}
                                className="w-[48%]"
                            >
                                <ChevronLeft className="mr-2 h-4 w-4" /> Previous
                            </Button>
                            <Button
                                variant="outline"
                                onClick={onNext}
                                disabled={!onNext}
                                className="w-[48%]"
                            >
                                Next <ChevronRight className="ml-2 h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}
