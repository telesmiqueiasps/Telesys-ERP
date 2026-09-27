import React, { useState, useEffect, useCallback } from "react";
import {
  HardDrive,
  CloudUpload,
  Download,
  RotateCcw,
  Trash2,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  FileCheck,
} from "lucide-react";
import { backupService } from "@/services/backupService";
import { BackupRecord } from "@/types/backup";

interface BackupModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const BackupModal: React.FC<BackupModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<"LOCAL" | "CLOUD">("LOCAL");
  const [localBackups, setLocalBackups] = useState<BackupRecord[]>([]);
  const [cloudBackups, setCloudBackups] = useState<BackupRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadBackups = useCallback(async () => {
    setLoading(true);
    setMessage(null);
    try {
      const loc = backupService.getLocalBackups();
      setLocalBackups(loc);
      const cld = await backupService.listCloudBackups();
      setCloudBackups(cld);
    } catch (err: any) {
      console.error("Erro ao carregar histórico de backups:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadBackups();
    }
  }, [isOpen, loadBackups]);

  if (!isOpen) return null;

  const handleCreateBackup = async () => {
    setCreating(true);
    setMessage(null);
    try {
      const result = await backupService.createBackup(true);
      if (result.cloudSynced) {
        setMessage({
          type: "success",
          text: "Backup criado localmente e salvo na nuvem com sucesso!",
        });
      } else if (result.error) {
        setMessage({
          type: "error",
          text: `Backup criado localmente, mas erro na nuvem: ${result.error}`,
        });
      } else {
        setMessage({
          type: "success",
          text: "Backup salvo localmente com sucesso.",
        });
      }
      await loadBackups();
    } catch (err: any) {
      setMessage({ type: "error", text: "Falha ao gerar backup." });
    } finally {
      setCreating(false);
    }
  };

  const handleRestoreLocal = (backupId: string) => {
    if (!window.confirm("Deseja restaurar este ponto de restauração local? Dados atuais serão substituídos.")) return;
    const ok = backupService.restoreBackup(backupId);
    if (ok) {
      alert("Restauração concluída com sucesso! Recarregando aplicação...");
      window.location.reload();
    } else {
      alert("Erro ao restaurar dados do backup local.");
    }
  };

  const handleDeleteLocal = (backupId: string) => {
    if (!window.confirm("Tem certeza que deseja excluir este backup local?")) return;
    backupService.deleteLocalBackup(backupId);
    loadBackups();
  };

  const handleDownloadCloud = async (filename: string) => {
    try {
      await backupService.downloadCloudBackup(filename);
    } catch (err: any) {
      alert(err?.message || "Erro ao baixar arquivo da nuvem.");
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/50">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <HardDrive className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Engine de Backup & Restauração 1-Clique</h2>
              <p className="text-xs text-slate-400">Backups compactados do SQLite local e cópias automáticas na Nuvem</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition"
          >
            ✕
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1">
          {message && (
            <div
              className={`p-3.5 rounded-lg flex items-center space-x-3 text-xs ${
                message.type === "success"
                  ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                  : "bg-amber-500/10 border border-amber-500/20 text-amber-400"
              }`}
            >
              {message.type === "success" ? (
                <CheckCircle className="w-4 h-4 flex-shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              )}
              <span>{message.text}</span>
            </div>
          )}

          {/* Top Banner Action */}
          <div className="bg-slate-850 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="space-y-1 text-left">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <FileCheck className="w-4 h-4 text-emerald-400" />
                <span>Backup em Tempo Real</span>
              </h3>
              <p className="text-xs text-slate-400">
                Gera um snapshot completo da sua base local SQLite e sincroniza na nuvem.
              </p>
            </div>

            <button
              onClick={handleCreateBackup}
              disabled={creating}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg transition shadow-md flex items-center space-x-2 disabled:opacity-50 flex-shrink-0"
            >
              {creating ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <CloudUpload className="w-4 h-4" />
                  <span>Criar Backup Agora</span>
                </>
              )}
            </button>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 space-x-4">
            <button
              onClick={() => setActiveTab("LOCAL")}
              className={`pb-2 text-xs font-bold transition flex items-center space-x-2 ${
                activeTab === "LOCAL"
                  ? "border-b-2 border-emerald-400 text-emerald-400"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <HardDrive className="w-4 h-4" />
              <span>Pontos de Restauração Locais ({localBackups.length})</span>
            </button>
            <button
              onClick={() => setActiveTab("CLOUD")}
              className={`pb-2 text-xs font-bold transition flex items-center space-x-2 ${
                activeTab === "CLOUD"
                  ? "border-b-2 border-emerald-400 text-emerald-400"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <CloudUpload className="w-4 h-4" />
              <span>Cópia Segura na Nuvem ({cloudBackups.length})</span>
            </button>
          </div>

          {/* Table */}
          {loading ? (
            <div className="flex justify-center py-10 text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin" />
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/60 text-slate-400 font-semibold uppercase border-b border-slate-800">
                  <tr>
                    <th className="p-3">Arquivo / Identificador</th>
                    <th className="p-3">Data & Hora</th>
                    <th className="p-3">Tamanho</th>
                    <th className="p-3">Integridade SHA-256</th>
                    <th className="p-3 text-right">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {(activeTab === "LOCAL" ? localBackups : cloudBackups).map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/30 transition">
                      <td className="p-3 font-mono font-medium text-white">{item.filename}</td>
                      <td className="p-3 text-slate-400">
                        {new Date(item.created_at).toLocaleString("pt-BR")}
                      </td>
                      <td className="p-3 font-mono text-slate-400">{formatSize(item.size_bytes)}</td>
                      <td className="p-3 font-mono text-[10px] text-slate-500">{item.hash || "Verificado OK"}</td>
                      <td className="p-3 text-right space-x-2">
                        {activeTab === "LOCAL" ? (
                          <>
                            <button
                              onClick={() => handleRestoreLocal(item.id)}
                              className="px-2 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded text-[11px] font-medium transition inline-flex items-center space-x-1"
                              title="Restaurar este estado"
                            >
                              <RotateCcw className="w-3 h-3" />
                              <span>Restaurar</span>
                            </button>
                            <button
                              onClick={() => handleDeleteLocal(item.id)}
                              className="p-1 text-slate-500 hover:text-red-400 transition"
                              title="Excluir Backup Local"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => handleDownloadCloud(item.filename)}
                            className="px-2 py-1 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded text-[11px] font-medium transition inline-flex items-center space-x-1"
                          >
                            <Download className="w-3 h-3" />
                            <span>Baixar</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}

                  {(activeTab === "LOCAL" ? localBackups : cloudBackups).length === 0 && (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-slate-500">
                        Nenhum arquivo de backup encontrado nesta seção.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs rounded-lg transition"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};
