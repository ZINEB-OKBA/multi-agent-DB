import { Injectable } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class AsfimService {

  protected API_URL = '/api/document-list';

  constructor(private http: HttpClient) {}

  /**
   * Recherche avec filtre
   */
  find(filter: any): Observable<any> {
    return this.http.post<any>(
        `${this.API_URL}/find`,
        filter
    );
  }

  /**
   * Pagination simple
   */
  findAll(page: number, size: number): Observable<any> {

    const payload = {
      page,
      size
    };

    return this.http.post<any>(
        `${this.API_URL}/find`,
        payload
    );
  }

  /**
   * Upload fichier
   */
  upload(formData: FormData): Observable<any> {
    return this.http.post(`${this.API_URL}/upload`, formData, {
      reportProgress: true,
      observe: 'events'
    });
  }

  /**
   * Suppression fichier
   */
  delete(id: number): Observable<any> {
    return this.http.delete(
        `${this.API_URL}/${id}`
    );
  }
}