import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class AmmcService {

  protected API_URL = '/api/ammc';

  constructor(private http: HttpClient) {}

  find(filter: any): Observable<any> {
    return this.http.post<any>(this.API_URL+ '/find', filter);
  }
}
