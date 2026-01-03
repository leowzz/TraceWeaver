import type { ColumnDef } from "@tanstack/react-table"
import { formatDistanceToNow } from "date-fns"
import type { SourceConfigPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { DataSourceActionsMenu } from "./DataSourceActionsMenu"

export type DataSourceTableData = SourceConfigPublic

const typeColors = {
  GIT: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  DAYFLOW:
    "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
  SIYUAN: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
}

export const columns: ColumnDef<DataSourceTableData>[] = [
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => (
      <div className="flex flex-col gap-0.5">
        <span className="font-medium">{row.original.name}</span>
        <span className="text-xs text-muted-foreground">
          ID: {row.original.id}
        </span>
      </div>
    ),
  },
  {
    accessorKey: "type",
    header: "Type",
    cell: ({ row }) => {
      const type = row.original.type
      return (
        <Badge variant="secondary" className={typeColors[type]}>
          {type}
        </Badge>
      )
    },
  },
  {
    accessorKey: "is_active",
    header: "Status",
    cell: ({ row }) => {
      const isActive = row.original.is_active
      return (
        <Badge variant={isActive ? "default" : "outline"}>
          {isActive ? "Active" : "Inactive"}
        </Badge>
      )
    },
  },
  {
    accessorKey: "created_at",
    header: "Created",
    cell: ({ row }) => {
      const date = new Date(row.original.created_at)
      return (
        <span className="text-sm text-muted-foreground">
          {formatDistanceToNow(date, { addSuffix: true })}
        </span>
      )
    },
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <DataSourceActionsMenu dataSource={row.original} />
      </div>
    ),
  },
]
