import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {HttpClient} from '@angular/common/http';
import {environment} from "../../../../environments/environment";

@Injectable({
    providedIn: 'root',
})
export class SmtpService {
    private API_URL = environment.apis.administration + '/smtp';

    constructor(private http: HttpClient) {}

    save(element: any): Observable<boolean> {
        return this.http.post<boolean>(this.API_URL + '/save', element);
    }

    get(): Observable<any> {
        return this.http.get<any>(this.API_URL + '/get');
    }

    testSmtp(): Observable<boolean> {
        return this.http.get<boolean>(this.API_URL + '/test');
    }
}