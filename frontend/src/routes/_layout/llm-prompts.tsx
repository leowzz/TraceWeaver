import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, Outlet, useMatch } from "@tanstack/react-router"
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
    component: LLMPromptsLayout,
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

function LLMPromptsLayout() {
    // Check if we're on a child route (e.g., /llm-prompts/1)
    const childMatch = useMatch({
        from: "/_layout/llm-prompts/$id",
        shouldThrow: false,
    })

    // If on child route, render Outlet (child content)
    if (childMatch) {
        return <Outlet />
    }

    // Otherwise render the list page
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
