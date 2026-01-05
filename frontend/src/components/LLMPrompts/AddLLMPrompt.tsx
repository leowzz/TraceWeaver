import { Link } from "@tanstack/react-router"
import { Plus } from "lucide-react"

import { Button } from "@/components/ui/button"

const AddLLMPrompt = () => {
    return (
        <Button asChild>
            <Link to="/llm-prompts/$id" params={{ id: "new" }}>
                <Plus className="mr-2" />
                Add Prompt
            </Link>
        </Button>
    )
}

export default AddLLMPrompt

