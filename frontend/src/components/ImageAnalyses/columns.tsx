import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { ImageAnalysisPublic } from "@/client"
import { createColumnHelper } from "@tanstack/react-table"
import { format } from "date-fns"
import { Eye } from "lucide-react"

export const columnHelper = createColumnHelper<ImageAnalysisPublic>()

interface ColumnsProps {
    onViewDetail: (analysis: ImageAnalysisPublic) => void
}

export const getColumns = ({ onViewDetail }: ColumnsProps) => [
    columnHelper.accessor("id", {
        header: "ID",
        cell: (info) => info.getValue(),
        size: 50,
    }),
    columnHelper.accessor("img_path", {
        header: "Image Path",
        cell: (info) => (
            <span className="truncate block max-w-[200px]" title={info.getValue()}>
                {info.getValue()}
            </span>
        ),
    }),
    columnHelper.accessor("status", {
        header: "Status",
        cell: (info) => {
            const status = info.getValue()
            const variant =
                status === "COMPLETED"
                    ? "default"
                    : status === "FAILED"
                        ? "destructive"
                        : "secondary"
            return <Badge variant={variant}>{status}</Badge>
        },
    }),
    columnHelper.accessor("model_name", {
        header: "Model",
        cell: (info) => info.getValue(),
    }),
    columnHelper.accessor("analysis_result", {
        header: "Result Preview",
        cell: (info) => {
            const result = info.getValue()
            return result ? (
                <span className="truncate block max-w-[300px]" title={result}>
                    {result}
                </span>
            ) : (
                <span className="text-muted-foreground italic">No result</span>
            )
        },
    }),
    columnHelper.accessor("created_at", {
        header: "Created At",
        cell: (info) => format(new Date(info.getValue()), "yyyy-MM-dd HH:mm:ss"),
    }),
    columnHelper.display({
        id: "actions",
        header: "Actions",
        cell: (info) => (
            <Button
                variant="ghost"
                size="icon"
                onClick={() => onViewDetail(info.row.original)}
                title="View Details"
            >
                <Eye className="h-4 w-4" />
            </Button>
        ),
    }),
]
