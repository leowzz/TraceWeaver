import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { type SourceConfigCreate, SourceConfigsService } from "@/client"
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
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  name: z.string().min(1, { message: "Name is required" }),
  type: z.enum(["GIT", "DAYFLOW", "SIYUAN"], {
    required_error: "Type is required",
  }),
  // Git config
  repo_path: z.string().optional(),
  branch: z.string().optional(),
  // Dayflow/SiYuan config
  api_url: z.string().url().optional().or(z.literal("")),
  api_token: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

const AddDataSource = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { user } = useAuth()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
      type: "GIT",
      repo_path: "",
      branch: "main",
      api_url: "",
      api_token: "",
    },
  })

  const selectedType = form.watch("type")

  const mutation = useMutation({
    mutationFn: (data: SourceConfigCreate) =>
      SourceConfigsService.createSourceConfig({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Data source created successfully")
      form.reset()
      setIsOpen(false)
    },
    onError: (error) => handleError(error, showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["source-configs"] })
    },
  })

  const onSubmit = (data: FormData) => {
    // Build config_payload based on type
    let config_payload = {}
    if (data.type === "GIT") {
      config_payload = {
        repo_path: data.repo_path,
        branch: data.branch || "main",
      }
    } else if (data.type === "DAYFLOW" || data.type === "SIYUAN") {
      config_payload = {
        api_url: data.api_url,
        api_token: data.api_token,
      }
    }

    const payload = {
      user_id: user!.id, // Non-null assertion since user is required
      name: data.name,
      type: data.type,
      config_payload,
      is_active: true,
    }

    mutation.mutate(payload)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2" />
          Add Data Source
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Data Source</DialogTitle>
          <DialogDescription>
            Configure a new data source connection.
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
                        placeholder="e.g., My Git Repository"
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
                name="type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Type <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="GIT">Git Repository</SelectItem>
                        <SelectItem value="DAYFLOW">Dayflow</SelectItem>
                        <SelectItem value="SIYUAN">SiYuan Notes</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {selectedType === "GIT" && (
                <>
                  <FormField
                    control={form.control}
                    name="repo_path"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          Repository Path{" "}
                          <span className="text-destructive">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            placeholder="/path/to/repository"
                            type="text"
                            {...field}
                            required
                          />
                        </FormControl>
                        <FormDescription>
                          Absolute path to the Git repository
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="branch"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Branch</FormLabel>
                        <FormControl>
                          <Input placeholder="main" type="text" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </>
              )}

              {(selectedType === "DAYFLOW" || selectedType === "SIYUAN") && (
                <>
                  <FormField
                    control={form.control}
                    name="api_url"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          API URL <span className="text-destructive">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            placeholder={
                              selectedType === "SIYUAN"
                                ? "http://localhost:6806"
                                : "https://api.dayflow.com"
                            }
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
                    name="api_token"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          API Token <span className="text-destructive">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Enter API token"
                            type="password"
                            {...field}
                            required
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </>
              )}
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

export default AddDataSource
