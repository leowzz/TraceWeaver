import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Pencil, TestTube } from "lucide-react"
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
  // Dayflow config
  db_path: z.string().optional(),
  // SiYuan config
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
        db_path: "",
        api_url: "",
        api_token: "",
      }
    } else if (dataSource.type === "DAYFLOW") {
      return {
        ...base,
        repo_path: "",
        branch: "",
        db_path: dataSource.config_payload?.db_path || "",
        api_url: "",
        api_token: "",
      }
    }
    return {
      ...base,
      repo_path: "",
      branch: "",
      db_path: "",
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
    onError: (error) => handleError.call(showErrorToast, error as any),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["source-configs"] })
    },
  })

  const testConnectionMutation = useMutation({
    mutationFn: async () => {
      // Validate form first
      const isValid = await form.trigger()
      if (!isValid) {
        throw new Error("请先填写所有必填字段")
      }

      // Get form data
      const formData = form.getValues()
      let config_payload = {}
      if (dataSource.type === "GIT") {
        config_payload = {
          repo_path: formData.repo_path,
          branch: formData.branch || "main",
        }
      } else if (dataSource.type === "DAYFLOW") {
        config_payload = {
          db_path: formData.db_path,
        }
      } else if (dataSource.type === "SIYUAN") {
        config_payload = {
          api_url: formData.api_url,
          api_token: formData.api_token,
        }
      }

      // Save temporarily
      await SourceConfigsService.updateSourceConfig({
        id: dataSource.id,
        requestBody: {
          config_payload,
        },
      })

      // Then test the connection
      return SourceConfigsService.testSourceConfigConnection({
        id: dataSource.id,
      })
    },
    onSuccess: (data) => {
      showSuccessToast(data.message || "连接测试成功")
    },
    onError: (error) => handleError.call(showErrorToast, error as any),
  })

  const onSubmit = (data: FormData) => {
    // Build config_payload based on type
    let config_payload = {}
    if (dataSource.type === "GIT") {
      config_payload = {
        repo_path: data.repo_path,
        branch: data.branch || "main",
      }
    } else if (dataSource.type === "DAYFLOW") {
      config_payload = {
        db_path: data.db_path,
      }
    } else if (dataSource.type === "SIYUAN") {
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

              {dataSource.type === "DAYFLOW" && (
                <FormField
                  control={form.control}
                  name="db_path"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Database Path{" "}
                        <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder="/Users/leo/Library/Application Support/Dayflow/chunks.sqlite"
                          type="text"
                          {...field}
                          required
                        />
                      </FormControl>
                      <FormDescription>
                        Absolute path to the Dayflow SQLite database file
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              {dataSource.type === "SIYUAN" && (
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
                            placeholder="http://localhost:6806"
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

            <DialogFooter className="flex items-center justify-between">
              <LoadingButton
                type="button"
                variant="outline"
                onClick={() => testConnectionMutation.mutate()}
                loading={testConnectionMutation.isPending}
                disabled={mutation.isPending}
              >
                <TestTube className="mr-2 h-4 w-4" />
                测试连接
              </LoadingButton>
              <div className="flex gap-2">
                <DialogClose asChild>
                  <Button variant="outline" disabled={mutation.isPending}>
                    Cancel
                  </Button>
                </DialogClose>
                <LoadingButton type="submit" loading={mutation.isPending}>
                  Save
                </LoadingButton>
              </div>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default EditDataSource
