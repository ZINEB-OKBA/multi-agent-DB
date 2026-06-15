import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {HttpClient} from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class AttemptAuthenticationsService {

  private API_URL = '/api/attempt-authentications';

  constructor(private http: HttpClient) {}

  find(filter: any): Observable<any> {
    return this.http.post<any>(this.API_URL+ '/find', filter);
  }

}
