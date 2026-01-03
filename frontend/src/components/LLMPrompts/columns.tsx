import type { ColumnDef } from "@tanstack/react-table"

import type { LLMPromptPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { LLMPromptActionsMenu } from "./LLMPromptActionsMenu"

export const columns: ColumnDef<LLMPromptPublic>[] = [
    {
        accessorKey: "name",
        header: "Name",
        cell: ({ row }) => (
            <span className="font-medium">{row.getValue("name")}</span>
        ),
    },
    {
        accessorKey: "content",
        header: "Content",
        cell: ({ row }) => {
            const content = row.getValue("content") as string
            const truncated = content.length > 80 ? content.slice(0, 80) + "..." : content
            return (
                <span className="text-muted-foreground text-sm" title={content}>
                    {truncated}
                </span>
            )
        },
    },
    {
        accessorKey: "is_active",
        header: "Status",
        cell: ({ row }) => (
            <Badge variant={row.getValue("is_active") ? "default" : "secondary"}>
                {row.getValue("is_active") ? "Active" : "Inactive"}
            </Badge>
        ),
    },
    {
        id: "actions",
        cell: ({ row }) => <LLMPromptActionsMenu prompt={row.original} />,
    },
]
