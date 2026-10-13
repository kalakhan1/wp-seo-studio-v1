import { apiClient } from "@/services/apiClient";
import type {
  BackupExportResponse,
  BackupImportReport,
  BackupImportRequest,
} from "@/types/backup";

export const backupApi = {
  exportBundle: (): Promise<BackupExportResponse> =>
    apiClient.get<BackupExportResponse>("/api/v1/backup/export"),

  importBundle: (payload: BackupImportRequest): Promise<BackupImportReport> =>
    apiClient.post<BackupImportReport>("/api/v1/backup/import", payload),
};