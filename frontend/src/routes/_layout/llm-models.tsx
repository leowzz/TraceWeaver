import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense } from "react"

import { LlmModelConfigsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import AddLLMModelConfig from "@/components/LLMModelConfigs/AddLLMModelConfig"
import { columns } from "@/components/LLMModelConfigs/columns"
import PendingItems from "@/components/Pending/PendingItems"

function getLLMModelConfigsQueryOptions() {
    return {
        queryFn: () =>
            LlmModelConfigsService.readLlmModelConfigs({ skip: 0, limit: 100 }),
        queryKey: ["llm-model-configs"],
    }
}

export const Route = createFileRoute("/_layout/llm-models")({
    component: LLMModels,
    head: () => ({
        meta: [
            {
                title: "LLM Models - TraceWeaver",
            },
        ],
    }),
})

function LLMModelConfigsTableContent() {
    const { data: configs } = useSuspenseQuery(getLLMModelConfigsQueryOptions())

    return <DataTable columns={columns} data={configs.data} />
}

function LLMModelConfigsTable() {
    return (
        <Suspense fallback={<PendingItems />}>
            <LLMModelConfigsTableContent />
        </Suspense>
    )
}

function LLMModels() {
    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">LLM Models</h1>
                    <p className="text-muted-foreground">
                        Configure LLM model connections for image analysis
                    </p>
                </div>
                <AddLLMModelConfig />
            </div>
            <LLMModelConfigsTable />
        </div>
    )
}
