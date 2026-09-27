import React from "react";
import { Sparkles, Download, X, ArrowUpCircle } from "lucide-react";
import { updaterService } from "@/services/updaterService";
import { UpdateCheckResponse } from "@/types/updater";

interface UpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  updateData: UpdateCheckResponse | null;
}

export const UpdateModal: React.FC<UpdateModalProps> = ({ isOpen, onClose, updateData }) => {
  if (!isOpen || !updateData || !updateData.update_available) return null;

  const handleUpdate = () => {
    updaterService.downloadUpdate(updateData.download_url);
    onClose();
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-md w-full bg-slate-900 border border-blue-500/40 rounded-2xl shadow-2xl p-5 space-y-4 animate-in slide-in-from-bottom-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2 text-blue-400 font-bold text-sm">
          <ArrowUpCircle className="w-5 h-5 text-blue-400 animate-bounce" />
          <span>Nova Versão {updateData.latest_version} Disponível!</span>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-2 text-xs text-slate-300">
        <p className="text-slate-400">
          Uma nova atualização do <span className="font-semibold text-white">Telesys ERP + PDV</span> está pronta.
        </p>

        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1.5 font-mono text-[11px] text-slate-300 max-h-36 overflow-y-auto">
          <div className="font-bold text-blue-400 flex items-center space-x-1 mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Novidades da Versão v{updateData.latest_version}:</span>
          </div>
          <p className="whitespace-pre-line leading-relaxed">{updateData.release_notes}</p>
        </div>
      </div>

      <div className="flex items-center justify-end space-x-3 pt-2">
        {!updateData.mandatory && (
          <button
            onClick={onClose}
            className="px-3.5 py-2 text-xs font-medium text-slate-400 hover:text-white transition"
          >
            Lembrar Mais Tarde
          </button>
        )}
        <button
          onClick={handleUpdate}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-lg transition flex items-center space-x-2"
        >
          <Download className="w-4 h-4" />
          <span>Baixar & Atualizar Agora</span>
        </button>
      </div>
    </div>
  );
};
