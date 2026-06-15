import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import {SessionStorageService} from "./session.storage.service";
import {firstValueFrom, Observable} from "rxjs";
import {User} from '../models/user';

const API_USERS_URL = `/api/auth`;

@Injectable({ providedIn: 'root' })
export class AuthenticationService {

  constructor(
    private http: HttpClient,
    private session: SessionStorageService,
    private router: Router
  ) {}

  attemptAuthentication(user: User): Observable<any> {
    return this.http.post(API_USERS_URL+ '/authenticate' , user)
  }


  register(user: User): Observable<boolean> {
    return this.http.post<boolean>(API_USERS_URL + '/register', user);
  }

  forgotPassword(email: string): Observable<boolean> {
    return this.http.post<boolean>(`${API_USERS_URL}/forgot-password`,
      email,
    );
  }

  async refreshToken(): Promise<string | null> {
    const refreshToken = this.session.getRefreshToken();
    if (!refreshToken) return null;

    try {
      const response: any = await firstValueFrom(
        this.http.post('/api/auth/refresh', {
          refreshToken: refreshToken
        })
      );

      this.session.setToken(response.accessToken);
      if (response.refreshToken) {
        this.session.setRefreshToken(response.refreshToken);
      }

      return response.accessToken;
    } catch (err) {
      return null;
    }

  }
  setNewPassword(object:any){
    return  this.http.post<any>(`${API_USERS_URL}/new-password`, object);
  }

  updatePassword(element: any): Observable<boolean> {
    return this.http.post<boolean>(API_USERS_URL+ '/update-password', element);
  }

  logout() {
    this.session.clear();
    this.router.navigate(['/auth/login']);
  }

}
