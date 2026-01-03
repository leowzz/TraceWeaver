import { useMutation } from "@tanstack/react-query"
import { EllipsisVertical, TestTube } from "lucide-react"
import { useState } from "react"

import { type SourceConfigPublic, SourceConfigsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import DeleteDataSource from "./DeleteDataSource"
import EditDataSource from "./EditDataSource"

interface DataSourceActionsMenuProps {
  dataSource: SourceConfigPublic
}

export const DataSourceActionsMenu = ({
  dataSource,
}: DataSourceActionsMenuProps) => {
  const [open, setOpen] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const testMutation = useMutation({
    mutationFn: () =>
      SourceConfigsService.testSourceConfigConnection({ id: dataSource.id }),
    onSuccess: (data) => {
      showSuccessToast(data.message || "Connection test successful")
    },
    onError: (error) => handleError(error, showErrorToast),
  })

  const handleTestConnection = (e: Event) => {
    e.preventDefault()
    testMutation.mutate()
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <EditDataSource
          dataSource={dataSource}
          onSuccess={() => setOpen(false)}
        />
        <DropdownMenuItem
          onSelect={handleTestConnection}
          disabled={testMutation.isPending}
        >
          <TestTube />
          {testMutation.isPending ? "Testing..." : "Test Connection"}
        </DropdownMenuItem>
        <DeleteDataSource
          dataSource={dataSource}
          onSuccess={() => setOpen(false)}
        />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
