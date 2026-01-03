import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense } from "react"

import { SourceConfigsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import AddDataSource from "@/components/DataSources/AddDataSource"
import {
  columns,
  type DataSourceTableData,
} from "@/components/DataSources/columns"
import PendingItems from "@/components/Pending/PendingItems"

function getSourceConfigsQueryOptions() {
  return {
    queryFn: () =>
      SourceConfigsService.readSourceConfigs({ skip: 0, limit: 100 }),
    queryKey: ["source-configs"],
  }
}

export const Route = createFileRoute("/_layout/datasources")({
  component: DataSources,
  head: () => ({
    meta: [
      {
        title: "Data Sources - TraceWeaver",
      },
    ],
  }),
})

function DataSourcesTableContent() {
  const { data: sourceConfigs } = useSuspenseQuery(
    getSourceConfigsQueryOptions(),
  )

  const tableData: DataSourceTableData[] = sourceConfigs.data

  return <DataTable columns={columns} data={tableData} />
}

function DataSourcesTable() {
  return (
    <Suspense fallback={<PendingItems />}>
      <DataSourcesTableContent />
    </Suspense>
  )
}

function DataSources() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Data Sources</h1>
          <p className="text-muted-foreground">
            Manage your external data source connections
          </p>
        </div>
        <AddDataSource />
      </div>
      <DataSourcesTable />
    </div>
  )
}
