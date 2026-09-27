import React, { useState, useEffect } from 'react';
import {
  Key,
  ShieldCheck,
  Smartphone,
  Laptop,
  AlertTriangle,
  RefreshCw,
  CheckCircle,
  HardDrive,
  Copy,
  Check,
} from 'lucide-react';
import { licenseService } from '../services/licenseService';
import { LicenseInfo, DeviceInfo } from '../types/license';

interface LicenseModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LicenseModal: React.FC<LicenseModalProps> = ({ isOpen, onClose }) => {
  const [license, setLicense] = useState<LicenseInfo | null>(null);
  const [devices, setDevices] = useState<DeviceInfo[]>([]);
  const [newKey, setNewKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [activating, setActivating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);

  const currentDeviceId = licenseService.getDeviceId();

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await licenseService.getCurrentLicense();
      setLicense(data);
      const devList = await licenseService.listDevices();
      setDevices(devList);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Erro ao carregar dados da licença.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim()) return;

    setActivating(true);
    setError(null);
    setSuccess(null);
    try {
      const updated = await licenseService.activateLicense(newKey.trim());
      setLicense(updated);
      setSuccess('Licença ativada e dispositivo vinculado com sucesso!');
      setNewKey('');
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Falha ao ativar a chave de licença.');
    } finally {
      setActivating(false);
    }
  };

  const handleRevoke = async (deviceId: string) => {
    if (!window.confirm('Tem certeza que deseja revogar o acesso deste terminal?')) return;
    try {
      await licenseService.revokeDevice(deviceId);
      setSuccess('Dispositivo revogado com sucesso.');
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Erro ao revogar dispositivo.');
    }
  };

  const handleCopyKey = () => {
    if (license?.license_key) {
      navigator.clipboard.writeText(license.license_key);
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  const graceInfo = licenseService.validateOfflineGrace();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/50">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-lg">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Licenciamento & Terminais</h2>
              <p className="text-xs text-slate-400">Gerencie a chave da licença, plano contratado e dispositivos autorizados</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center space-x-3 text-red-400 text-sm">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center space-x-3 text-emerald-400 text-sm">
              <CheckCircle className="w-5 h-5 flex-shrink-0" />
              <span>{success}</span>
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-12 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin" />
            </div>
          ) : (
            <>
              {/* License Status Card */}
              {license && (
                <div className="bg-slate-850 border border-slate-800 rounded-xl p-5 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Plano Atual</span>
                      <div className="flex items-center space-x-3 mt-1">
                        <span className="text-2xl font-extrabold text-blue-400">{license.plan_name}</span>
                        <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {license.status}
                        </span>
                      </div>
                    </div>

                    <div className="text-right">
                      <span className="text-xs text-slate-400">Terminais Ativos</span>
                      <p className="text-xl font-bold text-white">
                        {license.active_devices_count} / {license.max_devices}
                      </p>
                    </div>
                  </div>

                  {/* License Key & Grace Info */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 flex items-center justify-between">
                      <div className="space-y-1">
                        <span className="text-xs text-slate-500 block">Chave de Licença</span>
                        <span className="font-mono text-sm font-semibold text-slate-200">{license.license_key}</span>
                      </div>
                      <button
                        onClick={handleCopyKey}
                        className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition"
                        title="Copiar Chave"
                      >
                        {copiedKey ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>

                    <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 flex items-center space-x-3">
                      <HardDrive className="w-5 h-5 text-indigo-400 flex-shrink-0" />
                      <div>
                        <span className="text-xs text-slate-500 block">Tolerância Offline</span>
                        <span className="text-xs font-medium text-slate-300">
                          {graceInfo.valid
                            ? `Restam ${graceInfo.daysRemaining} dias de carência offline`
                            : graceInfo.reason}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Activation Form */}
              <div className="bg-slate-850 border border-slate-800 rounded-xl p-5 space-y-3">
                <div className="flex items-center space-x-2 text-slate-300 font-semibold text-sm">
                  <Key className="w-4 h-4 text-blue-400" />
                  <span>Ativar Nova Chave de Licença</span>
                </div>
                <form onSubmit={handleActivate} className="flex gap-3">
                  <input
                    type="text"
                    value={newKey}
                    onChange={(e) => setNewKey(e.target.value)}
                    placeholder="Insira sua chave (Ex: TELESYS-PRO-12345)"
                    className="flex-1 px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono text-sm"
                  />
                  <button
                    type="submit"
                    disabled={activating || !newKey.trim()}
                    className="px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-sm rounded-lg transition flex items-center space-x-2"
                  >
                    {activating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <span>Ativar</span>}
                  </button>
                </form>
              </div>

              {/* Devices Table */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-300 flex items-center space-x-2">
                    <Laptop className="w-4 h-4 text-blue-400" />
                    <span>Terminais Registrados ({devices.length})</span>
                  </h3>
                  <button
                    onClick={loadData}
                    className="text-xs text-blue-400 hover:text-blue-300 flex items-center space-x-1"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Atualizar</span>
                  </button>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-800 uppercase font-semibold">
                      <tr>
                        <th className="p-3">Terminal</th>
                        <th className="p-3">ID Dispositivo</th>
                        <th className="p-3">Última Conexão</th>
                        <th className="p-3">Status</th>
                        <th className="p-3 text-right">Ação</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                      {devices.map((dev) => {
                        const isCurrent = dev.device_id === currentDeviceId;
                        return (
                          <tr key={dev.id} className="hover:bg-slate-800/30 transition">
                            <td className="p-3 font-medium text-white flex items-center space-x-2">
                              <Smartphone className="w-4 h-4 text-slate-400" />
                              <span>{dev.device_name}</span>
                              {isCurrent && (
                                <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                                  Este Terminal
                                </span>
                              )}
                            </td>
                            <td className="p-3 font-mono text-slate-400 text-[11px]">{dev.device_id}</td>
                            <td className="p-3 text-slate-400">
                              {dev.last_heartbeat_at
                                ? new Date(dev.last_heartbeat_at).toLocaleString('pt-BR')
                                : 'Nunca'}
                            </td>
                            <td className="p-3">
                              {dev.status === 'AUTHORIZED' ? (
                                <span className="px-2 py-0.5 rounded text-[11px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                                  Autorizado
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded text-[11px] bg-red-500/10 text-red-400 border border-red-500/20 font-medium">
                                  Revogado
                                </span>
                              )}
                            </td>
                            <td className="p-3 text-right">
                              {dev.status === 'AUTHORIZED' && (
                                <button
                                  onClick={() => handleRevoke(dev.id)}
                                  className="px-2 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-[11px] rounded font-medium transition"
                                >
                                  Revogar
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                      {devices.length === 0 && (
                        <tr>
                          <td colSpan={5} className="p-6 text-center text-slate-500">
                            Nenhum terminal registrado até o momento.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-sm rounded-lg transition"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};
