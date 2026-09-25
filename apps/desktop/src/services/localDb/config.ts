export const LOCAL_PATHS = {
  BASE_DIR: "C:\\ProgramData\\telesys",
  DATA_DIR: "C:\\ProgramData\\telesys\\data",
  EMPRESAS_DIR: "C:\\ProgramData\\telesys\\data\\empresas",
  BACKUPS_DIR: "C:\\ProgramData\\telesys\\data\\backups",
  LOGS_DIR: "C:\\ProgramData\\telesys\\logs",
  CACHE_DIR: "C:\\ProgramData\\telesys\\cache",
  CONFIG_DIR: "C:\\ProgramData\\telesys\\config",
  MASTER_DB_NAME: "master.db",
};

export function getCompanyDbName(companyId: string): string {
  const sanitizedId = companyId.replace(/[^a-zA-Z0-9-]/g, "_");
  return `empresa_${sanitizedId}.db`;
}
