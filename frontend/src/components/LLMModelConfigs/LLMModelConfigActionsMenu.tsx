import { MoreHorizontal, Pencil, Trash2 } from "lucide-react"

import type { LLMModelConfigPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import DeleteLLMModelConfig from "./DeleteLLMModelConfig"
import EditLLMModelConfig from "./EditLLMModelConfig"

interface LLMModelConfigActionsMenuProps {
    config: LLMModelConfigPublic
}

export function LLMModelConfigActionsMenu({
    config,
}: LLMModelConfigActionsMenuProps) {
    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="h-8 w-8 p-0">
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal className="h-4 w-4" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <EditLLMModelConfig
                    config={config}
                    trigger={
                        <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                            <Pencil className="mr-2 h-4 w-4" />
                            Edit
                        </DropdownMenuItem>
                    }
                />
                <DeleteLLMModelConfig
                    config={config}
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
