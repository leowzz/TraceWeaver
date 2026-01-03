import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Pencil } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  type SourceConfigPublic,
  type SourceConfigUpdate,
  SourceConfigsService,
} from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
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
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  name: z.string().min(1, { message: "Name is required" }),
  // Git config
  repo_path: z.string().optional(),
  branch: z.string().optional(),
  // Dayflow/SiYuan config
  api_url: z.string().url().optional().or(z.literal("")),
  api_token: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

interface EditDataSourceProps {
  dataSource: SourceConfigPublic
  onSuccess: () => void
}

const EditDataSource = ({ dataSource, onSuccess }: EditDataSourceProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Extract config values based on type
  const getDefaultValues = () => {
    const base = { name: dataSource.name }
    if (dataSource.type === "GIT") {
      return {
        ...base,
        repo_path: dataSource.config_payload?.repo_path || "",
        branch: dataSource.config_payload?.branch || "main",
        api_url: "",
        api_token: "",
      }
    }
    return {
      ...base,
      repo_path: "",
      branch: "",
      api_url: dataSource.config_payload?.api_url || "",
      api_token: dataSource.config_payload?.api_token || "",
    }
  }

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: getDefaultValues(),
  })

  const mutation = useMutation({
    mutationFn: (data: SourceConfigUpdate) =>
      SourceConfigsService.updateSourceConfig({
        id: dataSource.id,
        requestBody: data,
      }),
    onSuccess: () => {
      showSuccessToast("Data source updated successfully")
      setIsOpen(false)
      onSuccess()
    },
    onError: (error) => handleError(error, showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["source-configs"] })
    },
  })

  const onSubmit = (data: FormData) => {
    // Build config_payload based on type
    let config_payload = {}
    if (dataSource.type === "GIT") {
      config_payload = {
        repo_path: data.repo_path,
        branch: data.branch || "main",
      }
    } else if (dataSource.type === "DAYFLOW" || dataSource.type === "SIYUAN") {
      config_payload = {
        api_url: data.api_url,
        api_token: data.api_token,
      }
    }

    const payload = {
      name: data.name,
      config_payload,
    }

    mutation.mutate(payload)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        onSelect={(e) => e.preventDefault()}
        onClick={() => setIsOpen(true)}
      >
        <Pencil />
        Edit
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <DialogHeader>
              <DialogTitle>Edit Data Source</DialogTitle>
              <DialogDescription>
                Update the configuration for this data source.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Type:</span>
                <Badge>{dataSource.type}</Badge>
              </div>

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

              {dataSource.type === "GIT" && (
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

              {(dataSource.type === "DAYFLOW" ||
                dataSource.type === "SIYUAN") && (
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
                                dataSource.type === "SIYUAN"
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

export default EditDataSource
