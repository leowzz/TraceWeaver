import { useMutation, useQuery } from "@tanstack/react-query"
import { Calendar, RefreshCw } from "lucide-react"
import { useState } from "react"

import { SourceConfigsService, type SyncRequest } from "@/client"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const DayflowSyncCard = () => {
  const { user } = useAuth()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [startDate, setStartDate] = useState<string>(
    () => new Date("2020-08-12").toISOString().split("T")[0]
  )

  // Query Dayflow source configs
  const { data: sourceConfigsData } = useQuery({
    queryKey: ["source-configs"],
    queryFn: () => SourceConfigsService.readSourceConfigs({ skip: 0, limit: 100 }),
  })

  // Find Dayflow config
  const dayflowConfig = sourceConfigsData?.data?.find(
    (config) => config.type === "DAYFLOW" && config.is_active
  )

  const syncMutation = useMutation({
    mutationFn: ({ id, startDate }: { id: number; startDate: string }) => {
      const syncRequest: SyncRequest = {
        start_date: new Date(startDate).toISOString(),
      }
      return SourceConfigsService.syncSourceConfig({
        id,
        requestBody: syncRequest,
      })
    },
    onSuccess: (data) => {
      showSuccessToast(
        `同步完成！获取 ${data.total_fetched} 条，新增 ${data.new_count} 条，更新 ${data.updated_count} 条，向量化 ${data.embedded_count} 条`
      )
    },
    onError: (error) => handleError(error, showErrorToast),
  })

  const handleSync = () => {
    if (!dayflowConfig) {
      showErrorToast("未找到 Dayflow 数据源配置，请先添加")
      return
    }
    syncMutation.mutate({ id: dayflowConfig.id, startDate })
  }

  if (!dayflowConfig) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Dayflow 同步</CardTitle>
          <CardDescription>
            未找到 Dayflow 数据源配置，请先在数据源页面添加
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Dayflow 同步
        </CardTitle>
        <CardDescription>
          从指定日期开始同步 Dayflow 时间记录并生成向量
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="start-date">同步开始日期</Label>
          <Input
            id="start-date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            max={new Date().toISOString().split("T")[0]}
          />
          <p className="text-sm text-muted-foreground">
            将同步从该日期到现在的所有活动
          </p>
        </div>

        {syncMutation.data && (
          <div className="rounded-md bg-muted p-3 text-sm">
            <p className="font-medium">上次同步结果：</p>
            <ul className="mt-1 space-y-1">
              <li>获取活动：{syncMutation.data.total_fetched} 条</li>
              <li>新增：{syncMutation.data.new_count} 条</li>
              <li>更新：{syncMutation.data.updated_count} 条</li>
              <li>向量化：{syncMutation.data.embedded_count} 条</li>
            </ul>
          </div>
        )}

        <LoadingButton
          onClick={handleSync}
          loading={syncMutation.isPending}
          className="w-full"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          开始同步
        </LoadingButton>
      </CardContent>
    </Card>
  )
}

export default DayflowSyncCard
