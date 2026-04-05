export interface SystemMetrics {
    osName?: string;
    osVersion?: string;
    cpuCores?: number;
    cpuUsage: number; // Matches SystemMetricsDto from backend  
    cpuLoadPercentage?: number; // legacy
    systemUptimeSeconds?: number;
    ramUsage: number; // Matches SystemMetricsDto from backend
    totalRam: number; // Matches SystemMetricsDto from backend
    usedRam: number; // Matches SystemMetricsDto from backend
    totalRamBytes?: number; // legacy
    availableRamBytes?: number; // legacy
    usedRamBytes?: number; // legacy
    totalDisk: number;
    usedDisk: number;
    totalDiskBytes?: number; // legacy
    freeDiskBytes?: number; // legacy
    usedDiskBytes?: number; // legacy
}
