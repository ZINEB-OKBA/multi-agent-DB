import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Collaborator {
  id?: number;
  collaborateur: string;
  dateDemarrage: string;
  profilProfessionnel: string;
  anciennete: string;
  salaire: number;
}

export interface Imputation {
  id?: number;
  collaborateur: string;
  collaborateurId?: number;
  projet: string;
  projetId?: number;
  mois: string;
  annee: string;
  nbrJours: number;
}

export interface Project {
  id?: number;
  name: string;
  description?: string;
  clientName: string;
  startDate: string;
  endDate: string;
  turnover: number;
  createdAt?: string;
  updatedAt?: string;
}

@Injectable({
  providedIn: 'root'
})
export class StaffingService {
  private readonly API = '/api/staffing';

  constructor(private http: HttpClient) {}

  getCollaborators(): Observable<Collaborator[]> {
    return this.http.get<Collaborator[]>(`${this.API}/collaborateurs`);
  }

  createCollaborator(collab: Collaborator): Observable<Collaborator> {
    return this.http.post<Collaborator>(`${this.API}/collaborateurs`, collab);
  }

  deleteCollaborator(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API}/collaborateurs/${id}`);
  }

  getImputations(): Observable<Imputation[]> {
    return this.http.get<Imputation[]>(`${this.API}/imputations`);
  }

  createImputation(imputation: Imputation): Observable<Imputation> {
    return this.http.post<Imputation>(`${this.API}/imputations`, imputation);
  }

  deleteImputation(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API}/imputations/${id}`);
  }

  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(`${this.API}/projets`);
  }

  createProject(proj: Project): Observable<Project> {
    return this.http.post<Project>(`${this.API}/projets`, proj);
  }

  deleteProject(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API}/projets/${id}`);
  }
}
