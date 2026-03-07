export interface SystemMetrics {
    osName: string;
    osVersion: string;
    cpuCores: number;
    cpuLoadPercentage: number;
    systemUptimeSeconds: number;
    totalRamBytes: number;
    availableRamBytes: number;
    usedRamBytes: number;
    totalDiskBytes: number;
    freeDiskBytes: number;
    usedDiskBytes: number;
}
