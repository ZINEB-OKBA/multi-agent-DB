import {Injectable, model} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { Project, DocumentResponse, DocumentUploadRequest } from '../../../models/project.model';

@Injectable({ providedIn: 'root' })
export class ProjectService {

    private readonly API = '/api';

    // --- État partagé entre composants ---
    // Le projet sélectionné persiste en mémoire pendant la session (pas de BDD)
    private _selectedProject$ = new BehaviorSubject<Project | null>(null);
    readonly selectedProject$ = this._selectedProject$.asObservable();

    constructor(private http: HttpClient) {}

    // ── Projets ──────────────────────────────────────────────────────────────

    getAllProjects(): Observable<Project[]> {
        return this.http.get<Project[]>(`${this.API}/projects`);
    }

    createProject(project: Partial<Project>): Observable<Project> {
        return this.http.post<Project>(`${this.API}/projects`, project);
    }

    deleteProject(id: number): Observable<void> {
        return this.http.delete<void>(`${this.API}/projects/${id}`);
    }

    // ── Sélection en mémoire (pas d'appel HTTP) ──────────────────────────────

    selectProject(project: Project): void {
        this._selectedProject$.next(project);
    }

    getSelectedProject(): Project | null {
        return this._selectedProject$.getValue();
    }

    clearSelection(): void {
        this._selectedProject$.next(null);
    }

    // ── Documents ─────────────────────────────────────────────────────────────

    getProjectDocuments(projectId: number): Observable<DocumentResponse[]> {
        return this.http.get<DocumentResponse[]>(`${this.API}/projects/${projectId}/documents`);
    }

    uploadDocument(request: DocumentUploadRequest): Observable<string> {
        return this.http.post<string>(`${this.API}/documents/upload`, request, {
            responseType: 'text' as 'json'
        });
    }

    deleteDocument(documentId: number): Observable<void> {
        return this.http.delete<void>(`${this.API}/documents/${documentId}`);
    }

    triggerIndexing(documentId: number): Observable<DocumentResponse> {
        return this.http.post<DocumentResponse>(`${this.API}/documents/${documentId}/index`, {});
    }
}