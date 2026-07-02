import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class BkamService {

  protected API_URL = '/api/bkam';

  constructor(private http: HttpClient) {}

  findBandeFluctuation(filter: any): Observable<any> {
    return this.http.post<any>(this.API_URL+ '/bande-fluctuation', filter);
  }

  findCoursBillets(filter: any): Observable<any> {
    return this.http.post<any>(this.API_URL+ '/cours-billets', filter);
  }

  findHistoriqueDecision(filter: any): Observable<any> {
    return this.http.post<any>(this.API_URL+ '/historique-decision', filter);
  }

  findIndiceMonia(filter: any): Observable<any> {
    return this.http.post<any>(this.API_URL+ '/indice-monia', filter);
  }

  findMarcheMonetaire(filter: any): Observable<any> {
    return this.http.post<any>(this.API_URL+ '/marche-monetaire', filter);
  }

  findReferenceRate(filter: any): Observable<any> {
    return this.http.post<any>(this.API_URL+ '/reference-rate', filter);
  }
  findOperationsPrincipales(filter: any): Observable<any> {
    return this.http.post<any>(this.API_URL+ '/operations-principales', filter);
  }
}
