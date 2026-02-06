import api from './api';

export interface ModuleResult {
    success: boolean;
    message: string;
    data: any;
    execution_time_ms: number;
}

const SCAN_TIMEOUT_MS = 120000; // 2 dakika (nmap taraması uzun sürebilir)

export const modulesApi = {
    execute: async (moduleName: string, mode: 'passive' | 'active' = 'active', config: any = {}): Promise<ModuleResult> => {
        const response = await api.post(
            `/modules/${moduleName}/execute`,
            { mode, config },
            { timeoutMs: SCAN_TIMEOUT_MS }
        );
        return response.data.result;
    },

    getCombinedStatus: async () => {
        const response = await api.get('/modules');
        return response.data;
    }
};
