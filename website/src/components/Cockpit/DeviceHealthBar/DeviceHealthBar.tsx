import React from 'react';
import { DeviceHealthBarProps } from './DeviceHealthBar.types';

export const DeviceHealthBar: React.FC<DeviceHealthBarProps> = ({
  deviceHealth,
  className = '',
}) => {
  const cpu = Math.max(
    0,
    Math.min(100, Math.round(deviceHealth?.cpuUsagePercent ?? 0))
  );
  const ram = Math.max(
    0,
    Math.min(100, Math.round(deviceHealth?.memoryPercent ?? 0))
  );

  const hasGpu = Boolean(
    deviceHealth?.capabilities?.gpuMonitoring &&
    deviceHealth?.gpu?.gpuUsagePercent !== null &&
    deviceHealth?.gpu?.gpuUsagePercent !== undefined
  );
  const gpu = hasGpu
    ? Math.max(
        0,
        Math.min(100, Math.round(deviceHealth.gpu.gpuUsagePercent ?? 0))
      )
    : null;

  const getStatusColor = (val: number) => {
    if (val >= 90) return { bar: 'bg-rose-500', text: 'text-rose-400' };
    if (val >= 75) return { bar: 'bg-amber-400', text: 'text-amber-300' };
    return { bar: 'bg-cyan-500/80', text: 'text-slate-300' };
  };

  const cpuColor = getStatusColor(cpu);
  const ramColor = getStatusColor(ram);
  const gpuColor =
    gpu !== null
      ? getStatusColor(gpu)
      : { bar: 'bg-slate-700', text: 'text-slate-500' };

  return (
    <div
      className={`flex items-center gap-2.5 bg-slate-900/90 border border-slate-800/80 px-2.5 py-1 rounded-xl text-xs font-mono select-none ${className}`}
      title={`Device Health (Passive 1 Hz)\nCPU: ${cpu}%\nRAM: ${ram}%\nGPU: ${gpu !== null ? `${gpu}%` : 'Unsupported'}\nSystem Pressure: ${deviceHealth?.systemPressure ?? 'nominal'}`}
    >
      {/* CPU Indicator */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
          CPU
        </span>
        <div className="w-9 h-1.5 bg-slate-800/90 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 rounded-full ${cpuColor.bar}`}
            style={{ width: `${Math.max(4, cpu)}%` }}
          />
        </div>
        <span className={`text-[10px] font-bold ${cpuColor.text}`}>{cpu}%</span>
      </div>

      <span className="text-slate-800 text-[10px]">•</span>

      {/* RAM Indicator */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
          RAM
        </span>
        <div className="w-9 h-1.5 bg-slate-800/90 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 rounded-full ${ramColor.bar}`}
            style={{ width: `${Math.max(4, ram)}%` }}
          />
        </div>
        <span className={`text-[10px] font-bold ${ramColor.text}`}>{ram}%</span>
      </div>

      <span className="text-slate-800 text-[10px]">•</span>

      {/* GPU Indicator */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
          GPU
        </span>
        {gpu !== null ? (
          <>
            <div className="w-9 h-1.5 bg-slate-800/90 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 rounded-full ${gpuColor.bar}`}
                style={{ width: `${Math.max(4, gpu)}%` }}
              />
            </div>
            <span className={`text-[10px] font-bold ${gpuColor.text}`}>
              {gpu}%
            </span>
          </>
        ) : (
          <span
            className="text-[10px] text-slate-500 font-mono"
            title="GPU telemetry unsupported on platform"
          >
            N/A
          </span>
        )}
      </div>
    </div>
  );
};
