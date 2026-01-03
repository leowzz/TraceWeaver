import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { type LLMPromptPublic, LlmPromptsService } from "@/client"
import {
    AlertDialog,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface DeleteLLMPromptProps {
    prompt: LLMPromptPublic
    trigger?: React.ReactNode
}

const DeleteLLMPrompt = ({ prompt, trigger }: DeleteLLMPromptProps) => {
    const [isOpen, setIsOpen] = useState(false)
    const queryClient = useQueryClient()
    const { showSuccessToast, showErrorToast } = useCustomToast()

    const mutation = useMutation({
        mutationFn: () => LlmPromptsService.deleteLlmPrompt({ id: prompt.id }),
        onSuccess: () => {
            showSuccessToast("LLM Prompt deleted successfully")
            setIsOpen(false)
        },
        onError: (error) => handleError.call(showErrorToast, error),
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ["llm-prompts"] })
        },
    })

    return (
        <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
            <AlertDialogTrigger asChild>
                {trigger || <Button variant="destructive">Delete</Button>}
            </AlertDialogTrigger>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Delete LLM Prompt</AlertDialogTitle>
                    <AlertDialogDescription>
                        Are you sure you want to delete "{prompt.name}"? This action cannot
                        be undone.
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel disabled={mutation.isPending}>
                        Cancel
                    </AlertDialogCancel>
                    <LoadingButton
                        variant="destructive"
                        onClick={() => mutation.mutate()}
                        loading={mutation.isPending}
                    >
                        Delete
                    </LoadingButton>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    )
}

export default DeleteLLMPrompt
