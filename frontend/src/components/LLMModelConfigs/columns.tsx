import type { ColumnDef } from "@tanstack/react-table"

import type { LLMModelConfigPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { LLMModelConfigActionsMenu } from "./LLMModelConfigActionsMenu"

export const columns: ColumnDef<LLMModelConfigPublic>[] = [
    {
        accessorKey: "name",
        header: "Name",
        cell: ({ row }) => (
            <span className="font-medium">{row.getValue("name")}</span>
        ),
    },
    {
        accessorKey: "provider",
        header: "Provider",
        cell: ({ row }) => (
            <Badge variant="outline">{row.getValue("provider")}</Badge>
        ),
    },
    {
        accessorKey: "model_id",
        header: "Model ID",
        cell: ({ row }) => (
            <code className="text-sm bg-muted px-1.5 py-0.5 rounded">
                {row.getValue("model_id")}
            </code>
        ),
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
        cell: ({ row }) => <LLMModelConfigActionsMenu config={row.original} />,
    },
]
