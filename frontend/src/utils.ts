import { ApiError } from "./client"

function extractErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    const errDetail = (err.body as { detail?: unknown })?.detail
    if (Array.isArray(errDetail) && errDetail.length > 0) {
      const first = errDetail[0] as { msg?: string }
      return first.msg ?? "Something went wrong."
    }
    return typeof errDetail === "string" ? errDetail : "Something went wrong."
  }
  if (err instanceof Error) {
    return err.message
  }
  return String(err)
}

/** Call with handleError.call(showErrorToast, error) */
export const handleError = function (
  this: (msg: string) => void,
  err: unknown,
) {
  this(extractErrorMessage(err))
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}
