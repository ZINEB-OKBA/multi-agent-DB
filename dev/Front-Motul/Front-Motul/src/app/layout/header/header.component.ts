import {Component, OnInit} from '@angular/core';
import {AuthenticationService} from '../../core/auth/authentication.service';
import {TranslateService} from "@ngx-translate/core";
import {SessionStorageService} from "../../core/auth/session.storage.service";
import {Router} from "@angular/router";
import {LanguageService} from "../../core/services/language.service";

@Component({
  standalone: false,
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent implements OnInit{

    protected user: any;
    protected currentLanguage: string;
    protected readonly localStorage = localStorage;

  constructor(
      private sessionStorage: SessionStorageService,
      private authService: AuthenticationService,
      private translateService: TranslateService,
      private router : Router,
      private languageService : LanguageService,
  ) {
    const storedLang = this.languageService.getCurrentLanguage();
    this.currentLanguage = storedLang ? storedLang : 'fr';
    this.translateService.use(this.currentLanguage);
  }

  ngOnInit(): void {
    this.getCurrentUser();
  }

  onLogout() {
    this.authService.logout();
  }

  protected useLanguage(language: string): void {
    this.translateService.use(language);

    this.languageService.changeLanguage(language);

    this.currentLanguage = language;
  }

  protected getCurrentUser() {
    this.user = this.sessionStorage.getUser();
  }

  openProfile(): void {
    const userId = JSON.parse(sessionStorage.getItem('user'))?.id;
    if (userId) {
      this.router.navigate(['/administration/utilisateurs/profile/'+ userId]);
    }
  }

}
