export interface UpdateCheckResponse {
  current_version: string;
  latest_version: string;
  update_available: boolean;
  mandatory: boolean;
  release_notes: string;
  download_url?: string | null;
  pub_date: string;
}
