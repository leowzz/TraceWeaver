# IMPORTANT: Client Regeneration Required

## Current State

The TypeScript API client has **NOT been regenerated** yet because the backend server wasn't running during development. All frontend components include temporary API client implementations using the Fetch API directly.

## Why This Matters

Once you start the backend server, you should regenerate the TypeScript client to:
1. Get proper type definitions for `SourceConfigPublic`, `SourceConfigCreate`, etc.
2. Replace temporary fetch implementations with the generated `SourceConfigsService`
3. Enable better type safety and autocomplete

## How to Regenerate

```bash
# Make sure backend server is running first
cd backend
# Install dependencies if needed
poetry install  # or pip install -r requirements.txt
# Start the server
uvicorn app.main:app --reload

# In another terminal, regenerate client
cd /Users/leo/Desktop/work/TraceWeaver
bash scripts/generate-client.sh
```

## Files That Need Updates After Regeneration

Once the client is regenerated, update these files to remove temporary implementations:

1. [AddDataSource.tsx](file:///Users/leo/Desktop/work/TraceWeaver/frontend/src/components/DataSources/AddDataSource.tsx)
   - Remove `SourceConfigsService` constant
   - Import from `@/client` instead

2. [EditDataSource.tsx](file:///Users/leo/Desktop/work/TraceWeaver/frontend/src/components/DataSources/EditDataSource.tsx)
   - Remove `SourceConfigsService` constant
   - Import from `@/client` instead

3. [DeleteDataSource.tsx](file:///Users/leo/Desktop/work/TraceWeaver/frontend/src/components/DataSources/DeleteDataSource.tsx)
   - Remove `SourceConfigsService` constant
   - Import from `@/client` instead

4. [DataSourceActionsMenu.tsx](file:///Users/leo/Desktop/work/TraceWeaver/frontend/src/components/DataSources/DataSourceActionsMenu.tsx)
   - Remove `SourceConfigsService` constant
   - Import from `@/client` instead

5. [datasources.tsx](file:///Users/leo/Desktop/work/TraceWeaver/frontend/src/routes/_layout/datasources.tsx)
   - Remove `SourceConfigsService` constant
   - Import from `@/client` instead

6. [columns.tsx](file:///Users/leo/Desktop/work/TraceWeaver/frontend/src/components/DataSources/columns.tsx)
   - Remove temporary type definitions (`SourceConfigPublic`, `DataSourceTableData`)
   - Import types from `@/client` instead

## Example Replacement

**Before (current temporary implementation):**
```typescript
const SourceConfigsService = {
  createSourceConfig: async ({ requestBody }: { requestBody: any }) => {
    const response = await fetch("/api/source-configs/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(requestBody),
    })
    if (!response.ok) throw new Error("Failed to create source config")
    return response.json()
  },
}
```

**After (with generated client):**
```typescript
import { SourceConfigsService, type SourceConfigCreate } from "@/client"

// Use directly:
mutation.mutate(data) // SourceConfigsService.createSourceConfig will be called by the mutation
```

The temporary implementations work correctly and follow the same interface, so the functionality is already complete. This is just a code quality improvement.
