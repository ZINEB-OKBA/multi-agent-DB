import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {HttpClient} from '@angular/common/http';

@Injectable({
    providedIn: 'root',
})
export class ConversationService {

    private API_URL = '/api/conversations';

    constructor(private http: HttpClient) {}

    find(filter: any): Observable<any> {
        return this.http.post<any>(this.API_URL+ '/find', filter);
    }

    get(id: number): Observable<any> {
        return this.http.get<any>(this.API_URL+ '/get/'+ id);
    }

    delete(id: number): Observable<boolean> {
        return this.http.get<boolean>(this.API_URL+ '/delete/'+ id);
    }

    send(message: any): Observable<any> {
        return this.http.post<any>(`${this.API_URL}/send`, message);
    }

    rename(conversation: any): Observable<any> {
        return this.http.post<any>(`${this.API_URL}/rename`, conversation);
    }

}
