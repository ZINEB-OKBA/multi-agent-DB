import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";


const API_URL = '/api/email-notification'

@Injectable({
    providedIn: 'root'
})
export class EmailNotificationConfigService{


    constructor(private http: HttpClient) {
    }

    find(): Observable<any> {
        return this.http.get<any>(API_URL+ '/find');
    }

    get(id: string): Observable<any> {
        return this.http.get<any>(API_URL+ '/get/'+ id);
    }


    save(element: any): Observable<any> {
        return this.http.post<any>(API_URL+ '/save', element);
    }


}
