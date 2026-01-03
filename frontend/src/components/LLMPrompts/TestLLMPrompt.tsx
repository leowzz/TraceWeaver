import { useMutation, useQuery } from "@tanstack/react-query"
import { ImageIcon, Loader2 } from "lucide-react"
import { useRef, useState } from "react"

import {
    type LLMPromptPublic,
    LlmModelConfigsService,
    LlmPromptsService,
} from "@/client"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface TestLLMPromptProps {
    prompt: LLMPromptPublic
    trigger?: React.ReactNode
}

const TestLLMPrompt = ({ prompt, trigger }: TestLLMPromptProps) => {
    const [isOpen, setIsOpen] = useState(false)
    const [selectedModelId, setSelectedModelId] = useState<string>("")
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [previewUrl, setPreviewUrl] = useState<string | null>(null)
    const [result, setResult] = useState<string | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)
    const { showErrorToast } = useCustomToast()

    // Fetch available LLM model configs
    const { data: modelsData } = useQuery({
        queryFn: () =>
            LlmModelConfigsService.readLlmModelConfigs({ skip: 0, limit: 100 }),
        queryKey: ["llm-model-configs"],
        enabled: isOpen,
    })

    const testMutation = useMutation({
        mutationFn: async (data: { modelConfigId: number; file: File }) => {
            // Use the SDK's testLlmPrompt method with formData
            return LlmPromptsService.testLlmPrompt({
                id: prompt.id,
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

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                {trigger || (
                    <Button variant="outline" size="sm">
                        Test
                    </Button>
                )}
            </DialogTrigger>
            <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Test Prompt: {prompt.name}</DialogTitle>
                    <DialogDescription>
                        Upload an image and select an LLM model to test this prompt.
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    {/* Prompt Preview */}
                    <div className="space-y-2">
                        <Label>Prompt Template</Label>
                        <div className="bg-muted p-3 rounded-md text-sm max-h-24 overflow-y-auto">
                            {prompt.content}
                        </div>
                    </div>

                    {/* Model Selection */}
                    <div className="space-y-2">
                        <Label>LLM Model</Label>
                        <Select value={selectedModelId} onValueChange={setSelectedModelId}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select an LLM model" />
                            </SelectTrigger>
                            <SelectContent>
                                {modelsData?.data
                                    .filter((m) => m.is_active)
                                    .map((model) => (
                                        <SelectItem key={model.id} value={model.id.toString()}>
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
                                <Button type="button" variant="ghost" onClick={handleReset}>
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
                            !selectedModelId || !selectedFile || testMutation.isPending
                        }
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
                            <div className="bg-muted p-4 rounded-md text-sm whitespace-pre-wrap max-h-64 overflow-y-auto">
                                {result}
                            </div>
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    )
}

export default TestLLMPrompt
