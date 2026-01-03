import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { type LLMModelConfigCreate, LlmModelConfigsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
    name: z.string().min(1, "Name is required"),
    provider: z.enum(["OPENAI", "ANTHROPIC", "OLLAMA"]),
    model_id: z.string().min(1, "Model ID is required"),
    base_url: z.string().url("Valid URL is required"),
    api_key: z.string().optional(),
    config: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

const AddLLMModelConfig = () => {
    const [isOpen, setIsOpen] = useState(false)
    const queryClient = useQueryClient()
    const { showSuccessToast, showErrorToast } = useCustomToast()

    const form = useForm<FormData>({
        resolver: zodResolver(formSchema),
        mode: "onBlur",
        criteriaMode: "all",
        defaultValues: {
            name: "",
            provider: "OPENAI",
            model_id: "",
            base_url: "",
            api_key: "",
            config: "{}",
        },
    })

    const mutation = useMutation({
        mutationFn: (data: LLMModelConfigCreate) =>
            LlmModelConfigsService.createLlmModelConfig({ requestBody: data }),
        onSuccess: () => {
            showSuccessToast("LLM Model Config created successfully")
            form.reset()
            setIsOpen(false)
        },
        onError: (error) => handleError.call(showErrorToast, error),
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ["llm-model-configs"] })
        },
    })

    const onSubmit = (data: FormData) => {
        let configObj = {}
        if (data.config) {
            try {
                configObj = JSON.parse(data.config)
            } catch {
                // Keep empty object if parse fails
            }
        }

        const payload: LLMModelConfigCreate = {
            name: data.name,
            provider: data.provider,
            model_id: data.model_id,
            base_url: data.base_url,
            api_key: data.api_key || undefined,
            config: configObj,
            is_active: true,
        }

        mutation.mutate(payload)
    }

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button>
                    <Plus className="mr-2" />
                    Add LLM Model
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Add LLM Model Config</DialogTitle>
                    <DialogDescription>
                        Configure a new LLM model connection.
                    </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)}>
                        <div className="grid gap-4 py-4">
                            <FormField
                                control={form.control}
                                name="name"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>
                                            Name <span className="text-destructive">*</span>
                                        </FormLabel>
                                        <FormControl>
                                            <Input
                                                placeholder="e.g., GPT-4 Vision"
                                                type="text"
                                                {...field}
                                                required
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="provider"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>
                                            Provider <span className="text-destructive">*</span>
                                        </FormLabel>
                                        <Select
                                            onValueChange={field.onChange}
                                            defaultValue={field.value}
                                        >
                                            <FormControl>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select a provider" />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                <SelectItem value="OPENAI">OpenAI</SelectItem>
                                                <SelectItem value="ANTHROPIC">Anthropic</SelectItem>
                                                <SelectItem value="OLLAMA">Ollama</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="model_id"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>
                                            Model ID <span className="text-destructive">*</span>
                                        </FormLabel>
                                        <FormControl>
                                            <Input
                                                placeholder="e.g., gpt-4-vision-preview"
                                                type="text"
                                                {...field}
                                                required
                                            />
                                        </FormControl>
                                        <FormDescription>
                                            The model identifier used by the provider
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="base_url"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>
                                            Base URL <span className="text-destructive">*</span>
                                        </FormLabel>
                                        <FormControl>
                                            <Input
                                                placeholder="https://api.openai.com/v1"
                                                type="url"
                                                {...field}
                                                required
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="api_key"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>API Key</FormLabel>
                                        <FormControl>
                                            <Input
                                                placeholder="sk-..."
                                                type="password"
                                                {...field}
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="config"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Additional Config (JSON)</FormLabel>
                                        <FormControl>
                                            <Textarea
                                                placeholder="{}"
                                                className="font-mono text-sm"
                                                {...field}
                                            />
                                        </FormControl>
                                        <FormDescription>
                                            Optional JSON configuration
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>

                        <DialogFooter>
                            <DialogClose asChild>
                                <Button variant="outline" disabled={mutation.isPending}>
                                    Cancel
                                </Button>
                            </DialogClose>
                            <LoadingButton type="submit" loading={mutation.isPending}>
                                Save
                            </LoadingButton>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    )
}

export default AddLLMModelConfig
