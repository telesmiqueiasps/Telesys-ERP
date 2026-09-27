export interface BackupRecord {
  id: string;
  filename: string;
  size_bytes: number;
  type: 'LOCAL' | 'CLOUD';
  created_at: string;
  hash?: string;
  status?: string;
}

export interface BackupCreateResult {
  record: BackupRecord;
  cloudSynced: boolean;
  error?: string;
}
