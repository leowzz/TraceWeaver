import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import { ArrowLeft, ImageIcon, Loader2 } from "lucide-react"
import { useRef, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
    type LLMPromptCreate,
    type LLMPromptUpdate,
    LlmModelConfigsService,
    LlmPromptsService,
} from "@/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
    name: z.string().min(1, "Name is required"),
    content: z.string().min(1, "Content is required"),
    is_active: z.boolean(),
})

type FormData = z.infer<typeof formSchema>

export const Route = createFileRoute("/_layout/llm-prompts/$id")({
    component: LLMPromptDetail,
    head: () => ({
        meta: [
            {
                title: "Edit Prompt - TraceWeaver",
            },
        ],
    }),
})

function LLMPromptDetail() {
    const { id } = Route.useParams()
    const isNewMode = id === "new"
    const promptId = isNewMode ? 0 : parseInt(id)
    const queryClient = useQueryClient()
    const navigate = useNavigate()
    const { showSuccessToast, showErrorToast } = useCustomToast()

    // State for test functionality
    const [selectedModelId, setSelectedModelId] = useState<string>("")
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [previewUrl, setPreviewUrl] = useState<string | null>(null)
    const [result, setResult] = useState<string | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Fetch prompt data (only for edit mode)
    const { data: prompt, isLoading: isLoadingPrompt } = useQuery({
        queryFn: () => LlmPromptsService.readLlmPrompt({ id: promptId }),
        queryKey: ["llm-prompt", promptId],
        enabled: !isNewMode,
    })

    // Fetch available LLM model configs
    const { data: modelsData } = useQuery({
        queryFn: () =>
            LlmModelConfigsService.readLlmModelConfigs({ skip: 0, limit: 100 }),
        queryKey: ["llm-model-configs"],
    })

    const form = useForm<FormData>({
        resolver: zodResolver(formSchema),
        mode: "onBlur",
        criteriaMode: "all",
        defaultValues: isNewMode
            ? {
                name: "",
                content: "",
                is_active: true,
            }
            : undefined,
        values: !isNewMode && prompt
            ? {
                name: prompt.name,
                content: prompt.content,
                is_active: prompt.is_active ?? true,
            }
            : undefined,
    })

    // Create mutation (for new mode)
    const createMutation = useMutation({
        mutationFn: (data: LLMPromptCreate) =>
            LlmPromptsService.createLlmPrompt({ requestBody: data }),
        onSuccess: (newPrompt) => {
            showSuccessToast("Prompt created successfully")
            queryClient.invalidateQueries({ queryKey: ["llm-prompts"] })
            // Navigate to the newly created prompt
            navigate({ to: "/llm-prompts/$id", params: { id: newPrompt.id.toString() } })
        },
        onError: (error) => handleError.call(showErrorToast, error),
    })

    // Update mutation (for edit mode)
    const updateMutation = useMutation({
        mutationFn: (data: LLMPromptUpdate) =>
            LlmPromptsService.updateLlmPrompt({
                id: promptId,
                requestBody: data,
            }),
        onSuccess: () => {
            showSuccessToast("Prompt updated successfully")
        },
        onError: (error) => handleError.call(showErrorToast, error),
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ["llm-prompts"] })
            queryClient.invalidateQueries({ queryKey: ["llm-prompt", promptId] })
        },
    })

    // Test mutation
    const testMutation = useMutation({
        mutationFn: async (data: { modelConfigId: number; file: File }) => {
            return LlmPromptsService.testLlmPrompt({
                id: promptId,
                formData: {
                    llm_model_config_id: data.modelConfigId,
                    image: data.file,
                },
            })
        },
        onSuccess: (data) => {
            setResult(data.result)
        },
        onError: (error) => handleError.call(showErrorToast, error),
    })

    const onSubmit = (data: FormData) => {
        if (isNewMode) {
            createMutation.mutate({
                name: data.name,
                content: data.content,
                is_active: data.is_active,
            })
        } else {
            updateMutation.mutate(data)
        }
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            setSelectedFile(file)
            setPreviewUrl(URL.createObjectURL(file))
            setResult(null)
        }
    }

    const handleTest = () => {
        if (!selectedModelId || !selectedFile) return

        testMutation.mutate({
            modelConfigId: parseInt(selectedModelId),
            file: selectedFile,
        })
    }

    const handleReset = () => {
        setSelectedFile(null)
        setPreviewUrl(null)
        setResult(null)
        if (fileInputRef.current) {
            fileInputRef.current.value = ""
        }
    }

    // Loading state (only for edit mode)
    if (!isNewMode && isLoadingPrompt) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        )
    }

    // Not found state (only for edit mode)
    if (!isNewMode && !prompt) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <p className="text-muted-foreground">Prompt not found</p>
                <Button asChild variant="outline">
                    <Link to="/llm-prompts">Back to LLM Prompts</Link>
                </Button>
            </div>
        )
    }

    const isSaving = createMutation.isPending || updateMutation.isPending

    return (
        <div className="flex flex-col gap-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button asChild variant="ghost" size="icon">
                        <Link to="/llm-prompts">
                            <ArrowLeft className="h-5 w-5" />
                        </Link>
                    </Button>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">
                            {isNewMode ? "Add Prompt" : "Edit Prompt"}
                        </h1>
                        <p className="text-muted-foreground">
                            {isNewMode
                                ? "Create a new prompt template"
                                : prompt?.name}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <Label htmlFor="is-active">Active</Label>
                        <Switch
                            id="is-active"
                            checked={form.watch("is_active")}
                            onCheckedChange={(checked: boolean) =>
                                form.setValue("is_active", checked)
                            }
                        />
                    </div>
                    <LoadingButton
                        loading={isSaving}
                        onClick={form.handleSubmit(onSubmit)}
                    >
                        {isNewMode ? "Create Prompt" : "Save Changes"}
                    </LoadingButton>
                </div>
            </div>

            {/* Main Content - Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column - Edit Form */}
                <Card>
                    <CardHeader>
                        <CardTitle>Prompt Editor</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Form {...form}>
                            <form className="space-y-6">
                                <FormField
                                    control={form.control}
                                    name="name"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>
                                                Name{" "}
                                                <span className="text-destructive">
                                                    *
                                                </span>
                                            </FormLabel>
                                            <FormControl>
                                                <Input
                                                    type="text"
                                                    placeholder="e.g., Screenshot Analysis"
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
                                    name="content"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>
                                                Prompt Content{" "}
                                                <span className="text-destructive">
                                                    *
                                                </span>
                                            </FormLabel>
                                            <FormControl>
                                                <Textarea
                                                    className="min-h-[60vh] font-mono text-sm"
                                                    placeholder="Analyze this image and describe..."
                                                    {...field}
                                                    required
                                                />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </form>
                        </Form>
                    </CardContent>
                </Card>

                {/* Right Column - Test Panel */}
                <Card>
                    <CardHeader>
                        <CardTitle>Test Prompt</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {isNewMode ? (
                            <div className="flex items-center justify-center h-48 text-muted-foreground">
                                Save the prompt first to test it
                            </div>
                        ) : (
                            <>
                                {/* Model Selection */}
                                <div className="space-y-2">
                                    <Label>LLM Model</Label>
                                    <Select
                                        value={selectedModelId}
                                        onValueChange={setSelectedModelId}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select an LLM model" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {modelsData?.data
                                                .filter((m) => m.is_active)
                                                .map((model) => (
                                                    <SelectItem
                                                        key={model.id}
                                                        value={model.id.toString()}
                                                    >
                                                        {model.name} ({model.model_id})
                                                    </SelectItem>
                                                ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                {/* Image Upload */}
                                <div className="space-y-2">
                                    <Label>Image</Label>
                                    <div className="flex gap-2">
                                        <input
                                            ref={fileInputRef}
                                            type="file"
                                            accept="image/*"
                                            onChange={handleFileChange}
                                            className="hidden"
                                            id="test-image-upload"
                                        />
                                        <Button
                                            type="button"
                                            variant="outline"
                                            onClick={() => fileInputRef.current?.click()}
                                        >
                                            <ImageIcon className="mr-2 h-4 w-4" />
                                            Choose Image
                                        </Button>
                                        {selectedFile && (
                                            <Button
                                                type="button"
                                                variant="ghost"
                                                onClick={handleReset}
                                            >
                                                Clear
                                            </Button>
                                        )}
                                    </div>
                                    {previewUrl && (
                                        <div className="mt-2">
                                            <img
                                                src={previewUrl}
                                                alt="Preview"
                                                className="max-h-48 rounded-md object-contain"
                                            />
                                        </div>
                                    )}
                                </div>

                                {/* Test Button */}
                                <Button
                                    onClick={handleTest}
                                    disabled={
                                        !selectedModelId ||
                                        !selectedFile ||
                                        testMutation.isPending
                                    }
                                    className="w-full"
                                >
                                    {testMutation.isPending ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Analyzing...
                                        </>
                                    ) : (
                                        "Run Test"
                                    )}
                                </Button>

                                {/* Result */}
                                {result && (
                                    <div className="space-y-2">
                                        <Label>Analysis Result</Label>
                                        <div className="bg-muted p-4 rounded-md text-sm whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                                            {result}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
