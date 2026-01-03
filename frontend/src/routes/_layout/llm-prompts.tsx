import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense } from "react"

import { LlmPromptsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import AddLLMPrompt from "@/components/LLMPrompts/AddLLMPrompt"
import { columns } from "@/components/LLMPrompts/columns"
import PendingItems from "@/components/Pending/PendingItems"

function getLLMPromptsQueryOptions() {
    return {
        queryFn: () => LlmPromptsService.readLlmPrompts({ skip: 0, limit: 100 }),
        queryKey: ["llm-prompts"],
    }
}

export const Route = createFileRoute("/_layout/llm-prompts")({
    component: LLMPrompts,
    head: () => ({
        meta: [
            {
                title: "LLM Prompts - TraceWeaver",
            },
        ],
    }),
})

function LLMPromptsTableContent() {
    const { data: prompts } = useSuspenseQuery(getLLMPromptsQueryOptions())

    return <DataTable columns={columns} data={prompts.data} />
}

function LLMPromptsTable() {
    return (
        <Suspense fallback={<PendingItems />}>
            <LLMPromptsTableContent />
        </Suspense>
    )
}

function LLMPrompts() {
    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">LLM Prompts</h1>
                    <p className="text-muted-foreground">
                        Manage prompt templates for image analysis
                    </p>
                </div>
                <AddLLMPrompt />
            </div>
            <LLMPromptsTable />
        </div>
    )
}
