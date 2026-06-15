import { Component } from '@angular/core';
import {Router} from "@angular/router";

@Component({
  selector: 'app-bkam-landing',
  standalone: false,
  templateUrl: './bkam-landing.component.html',
  styleUrl: './bkam-landing.component.scss'
})
export class BkamLandingComponent {

  constructor(
      private router: Router,
  ) {
  }

  navigate(toComponent: string) {
    if (!toComponent || toComponent.trim() === '') {
      this.router.navigateByUrl('/data-base', { replaceUrl: true });
      return;
    }
    this.router.navigateByUrl(`/data-base/${toComponent}`);
  }


}
