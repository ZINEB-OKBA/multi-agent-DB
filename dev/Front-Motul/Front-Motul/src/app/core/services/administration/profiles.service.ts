import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {HttpClient} from '@angular/common/http';

const API_URL = '/api/profiles';

@Injectable({
  providedIn: 'root',
})
export class ProfilesService {
  constructor(private http: HttpClient) {}

  find(filter: any): Observable<any> {
    return this.http.post<any>(API_URL+ '/find', filter);
  }

  get(id: string): Observable<any> {
    return this.http.get<any>(API_URL+ '/get/'+ id);
  }

  save(element: any): Observable<any> {
    return this.http.post<any>(API_URL+ '/save', element);
  }

  delete(id: number): Observable<boolean> {
    return this.http.get<boolean>(API_URL+ '/delete/'+ id);
  }

  getModules(): Observable<any> {
    return this.http.get<any>(API_URL+ '/modules');
  }

  getRoles(module: any): Observable<any> {
    return this.http.post<any>(API_URL + '/roles-by-module', module);
  }


}
