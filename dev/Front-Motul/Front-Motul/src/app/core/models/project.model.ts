export interface Project {
    id: number;
    name: string;
    description?: string;
    createdAt?: string;
}

export interface DocumentResponse {
    id: number;
    fileName: string;
    projectId: number;
    projectName: string;
    isIndexed: boolean;
    indexing: boolean;
    indexedAt?: string;
    indexError?: string;
    uploadedAt: string;
}

export interface DocumentUploadRequest {
    projectId: number;
    fileName: string;
    content: string; // base64 avec préfixe data:...
}

export type DocumentType = 'pdf' | 'excel';

export const PDF_EXTENSIONS  = ['.pdf', '.doc', '.docx'];
export const EXCEL_EXTENSIONS = ['.xlsx', '.xls', '.xlsm', '.csv'];