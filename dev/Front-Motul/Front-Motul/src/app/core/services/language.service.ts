import { Injectable } from '@angular/core';
import {TranslateService} from "@ngx-translate/core";
import {CookieService} from "ngx-cookie-service";

@Injectable({
  providedIn: 'root'
})
export class LanguageService {

  private readonly cookieKey = 'lang';
  private readonly defaultLang = 'fr';

  constructor(
      private translate: TranslateService,
      private cookieService : CookieService
  ) {}

  /**
   * Initialize language based on cookie or fallback
   */
  initLanguage(): void {
    const lang = this.cookieService.get(this.cookieKey);

    if (lang) {
      this.translate.use(lang);
    } else {
      this.translate.use(this.defaultLang);
      this.cookieService.set(this.cookieKey, this.defaultLang, 365);
    }
  }

  /**
   * Change language and update cookie
   */
  changeLanguage(lang: string): void {
    this.translate.use(lang);
    this.cookieService.set(this.cookieKey, lang, 365);
  }

  /**
   * Get current language
   */
  getCurrentLanguage(): string {
    return this.cookieService.get(this.cookieKey) || this.defaultLang;
  }
}
