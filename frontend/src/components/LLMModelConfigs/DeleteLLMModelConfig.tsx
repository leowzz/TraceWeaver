import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { type LLMModelConfigPublic, LlmModelConfigsService } from "@/client"
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

interface DeleteLLMModelConfigProps {
    config: LLMModelConfigPublic
    trigger?: React.ReactNode
}

const DeleteLLMModelConfig = ({
    config,
    trigger,
}: DeleteLLMModelConfigProps) => {
    const [isOpen, setIsOpen] = useState(false)
    const queryClient = useQueryClient()
    const { showSuccessToast, showErrorToast } = useCustomToast()

    const mutation = useMutation({
        mutationFn: () =>
            LlmModelConfigsService.deleteLlmModelConfig({ id: config.id }),
        onSuccess: () => {
            showSuccessToast("LLM Model Config deleted successfully")
            setIsOpen(false)
        },
        onError: (error) => handleError.call(showErrorToast, error),
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ["llm-model-configs"] })
        },
    })

    return (
        <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
            <AlertDialogTrigger asChild>
                {trigger || <Button variant="destructive">Delete</Button>}
            </AlertDialogTrigger>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Delete LLM Model Config</AlertDialogTitle>
                    <AlertDialogDescription>
                        Are you sure you want to delete "{config.name}"? This action cannot
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

export default DeleteLLMModelConfig
