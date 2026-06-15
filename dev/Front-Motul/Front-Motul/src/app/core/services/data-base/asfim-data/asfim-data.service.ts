import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent } from "@angular/common/http";
import { Observable } from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class AsfimDataService {

  protected API_URL = '/api/project-landing';

  constructor(private http: HttpClient) {}

  /**
   * Recherche avec filtres et pagination
   */
  find(filter: any): Observable<any> {
    return this.http.post<any>(`${this.API_URL}/find`, filter);
  }

  /**
   * Upload de fichiers CSV/Excel avec suivi de progression
   * @param formData Contient le fichier, la catégorie et les paramètres d'indexation
   * @returns Un Observable d'événements HTTP (sent, progress, response)
   */
  upload(formData: FormData): Observable<HttpEvent<any>> {
    return this.http.post<any>(`${this.API_URL}/upload`, formData, {
      reportProgress: true, // Active le suivi de progression
      observe: 'events'     // Permet de recevoir les événements HttpEventType
    });
  }
}