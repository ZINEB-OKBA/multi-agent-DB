import {Component, AfterViewInit, Renderer2, OnInit} from '@angular/core';
import {NavigationEnd, Router, RouterOutlet} from '@angular/router';
import {KtuiLoader} from './core/helpers/ktui.loader';
import {filter} from 'rxjs';
import {NgIf} from "@angular/common";
import {TranslateService} from "@ngx-translate/core";
import {LanguageService} from "./core/services/language.service";

@Component({
    selector: 'app-root',
    imports: [RouterOutlet, NgIf],
    templateUrl: './app.component.html',
    standalone: true,
    styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  title = 'capital-trust-host';
  isAuthPage = false;
  constructor(private router: Router, private ktui: KtuiLoader, private languageService : LanguageService) {
      this.languageService.initLanguage();
  }

    ngOnInit(): void {
        this.ktui.initKtui();

        this.router.events
            .pipe(filter(event => event instanceof NavigationEnd))
            .subscribe((event: NavigationEnd) => {
                this.ktui.initKtui();

                this.isAuthPage = event.urlAfterRedirects.includes('/auth');
            }); 
    }


}
