import { MoreHorizontal, Pencil, Play, Trash2 } from "lucide-react"

import type { LLMPromptPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import DeleteLLMPrompt from "./DeleteLLMPrompt"
import EditLLMPrompt from "./EditLLMPrompt"
import TestLLMPrompt from "./TestLLMPrompt"

interface LLMPromptActionsMenuProps {
    prompt: LLMPromptPublic
}

export function LLMPromptActionsMenu({ prompt }: LLMPromptActionsMenuProps) {
    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="h-8 w-8 p-0">
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal className="h-4 w-4" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <TestLLMPrompt
                    prompt={prompt}
                    trigger={
                        <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                            <Play className="mr-2 h-4 w-4" />
                            Test
                        </DropdownMenuItem>
                    }
                />
                <DropdownMenuSeparator />
                <EditLLMPrompt
                    prompt={prompt}
                    trigger={
                        <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                            <Pencil className="mr-2 h-4 w-4" />
                            Edit
                        </DropdownMenuItem>
                    }
                />
                <DeleteLLMPrompt
                    prompt={prompt}
                    trigger={
                        <DropdownMenuItem
                            onSelect={(e) => e.preventDefault()}
                            className="text-destructive"
                        >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                        </DropdownMenuItem>
                    }
                />
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
