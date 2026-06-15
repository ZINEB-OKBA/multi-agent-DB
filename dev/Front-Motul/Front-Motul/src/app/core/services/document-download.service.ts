import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpResponse } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class DocumentDownloadService {

    private readonly API = '/api';

    constructor(private http: HttpClient) {}

    downloadById(documentId: number, fallbackFileName?: string): void {
        const url = `${this.API}/documents/${documentId}/download`;

        // Récupère le token depuis le localStorage (même clé que votre AuthService)
        const token = localStorage.getItem('access_token')
            || localStorage.getItem('token')
            || localStorage.getItem('jwt');

        const headers = token
            ? new HttpHeaders({ 'Authorization': `Bearer ${token}` })
            : new HttpHeaders();

        this.http.get(url, {
            responseType: 'blob',
            observe: 'response',
            headers                          // ← token ajouté manuellement
        }).subscribe({
            next: (response: HttpResponse<Blob>) => {
                const blob = response.body;
                if (!blob) { console.error('Réponse vide'); return; }
                const fileName = this.extractFileName(response, documentId, fallbackFileName);
                const correctedBlob = this.fixBlobType(blob, fileName);
                this.triggerDownload(correctedBlob, fileName);
            },
            error: (err) => {
                console.error('Erreur téléchargement:', err);
                alert('Erreur téléchargement — vérifiez F12.');
            }
        });
    }

    // ... reste du service inchangé (extractFileName, fixBlobType, triggerDownload)

    private extractFileName(
        response: HttpResponse<Blob>,
        documentId: number,
        fallback?: string
    ): string {
        const cd = response.headers.get('content-disposition') || '';
        let name = '';

        // Supporte filename*=UTF-8''... (RFC 5987)
        const utf8Match = cd.match(/filename\*=UTF-8''([^;]+)/i);
        if (utf8Match?.[1]) name = decodeURIComponent(utf8Match[1].trim());

        // Supporte filename="..." ou filename=...
        if (!name) {
            const simpleMatch = cd.match(/filename="?([^";]+)"?/i);
            if (simpleMatch?.[1]) name = simpleMatch[1].trim();
        }

        if (!name && fallback) name = fallback;

        if (!name) {
            const ext = this.mimeToExtension(response.body?.type || '');
            name = `document_${documentId}${ext}`;
        }

        return name;
    }

    /**
     * FIX PRINCIPAL :
     * Spring Boot renvoie APPLICATION_OCTET_STREAM pour forcer le téléchargement.
     * Le navigateur voit "octet-stream" et ne sait pas quel programme utiliser.
     * On recrée le Blob avec le bon MIME déduit de l'extension du fichier.
     * Résultat : Windows/Mac sait qu'un .docx s'ouvre avec Word, un .pdf avec Adobe, etc.
     */
    private fixBlobType(blob: Blob, fileName: string): Blob {
        const ext = fileName.split('.').pop()?.toLowerCase() || '';

        const mimeMap: Record<string, string> = {
            'pdf'  : 'application/pdf',
            'docx' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc'  : 'application/msword',
            'xlsx' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls'  : 'application/vnd.ms-excel',
            'xlsm' : 'application/vnd.ms-excel.sheet.macroEnabled.12',
            'csv'  : 'text/csv',
        };

        const correctMime = mimeMap[ext] || 'application/octet-stream';
        if (blob.type === correctMime) return blob;
        return new Blob([blob], { type: correctMime });
    }

    private triggerDownload(blob: Blob, fileName: string): void {
        const url  = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href  = url;
        link.setAttribute('download', fileName);
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
    }

    private mimeToExtension(mime: string): string {
        const map: Record<string, string> = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-excel': '.xls',
            'text/csv': '.csv',
        };
        return map[mime] || '';
    }
}