import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {HttpClient} from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class UserService {

  private API_URL = '/api/users';

  constructor(private http: HttpClient) {}

  find(filter: any): Observable<any> {
    return this.http.post<any>(this.API_URL+ '/find', filter);
  }

  get(id: string): Observable<any> {
    return this.http.get<any>(this.API_URL+ '/get/'+ id);
  }

  save(element: any): Observable<any> {
    return this.http.post<any>(this.API_URL+ '/save', element);
  }

  delete(id: number): Observable<boolean> {
    return this.http.get<boolean>(this.API_URL+ '/delete/'+ id);
  }

}
