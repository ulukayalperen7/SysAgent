export interface ApiResponse<T> {
    status: string;
    message: string;
    data: T | null;
    timestamp: string;
}
