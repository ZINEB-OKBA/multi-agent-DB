import {Injectable} from '@angular/core';
import {jwtDecode} from "jwt-decode";
import {RoleEnum} from '../enums/role.enum';
import {User} from '../models/user';

const USER = 'user';
const TOKEN = 'token';
const REFRESH_TOKEN = 'refresh-token';

@Injectable({providedIn: 'root'})
export class SessionStorageService {

  public clear() {
    window.sessionStorage.removeItem(USER);
    window.sessionStorage.removeItem(TOKEN);
    window.sessionStorage.removeItem(REFRESH_TOKEN);
  }

  private getDecodedToken(): any {
    try {
      return jwtDecode(this.getToken());
    } catch(Error) {
      return null;
    }
  }

  public getAuthority(): Array<RoleEnum> {
    const token = this.getDecodedToken();
    return token?.authorities;
  }

  public hasRole(role: RoleEnum): boolean{
    return this.getAuthority().indexOf(role) > -1;
  }

  public getToken(): string {
    return sessionStorage.getItem(TOKEN);
  }

  public getRefreshToken(): string {
    return sessionStorage.getItem(REFRESH_TOKEN);
  }

  public getUser(): User {
    return JSON.parse(sessionStorage.getItem(USER));
  }

  public setUser(user: User) {
    window.sessionStorage.removeItem(USER);
    window.sessionStorage.setItem(USER, JSON.stringify(user));
    this.setToken(user.accessToken);
    this.setRefreshToken(user.refreshToken);
  }

  public setToken(token: string) {
    window.sessionStorage.removeItem(TOKEN);
    window.sessionStorage.setItem(TOKEN, token);
  }

  public setRefreshToken(refreshToken: string) {
    window.sessionStorage.removeItem(REFRESH_TOKEN);
    window.sessionStorage.setItem(REFRESH_TOKEN, refreshToken);
  }

  get parameters(): string {
    return this.getUser()?.parameters
  }


}
