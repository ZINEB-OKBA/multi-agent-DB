import {AfterViewInit, Component, Renderer2} from '@angular/core';
import {Menu} from '../../core/menu/nav.service';

@Component({
  standalone: false,
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrl: './admin.component.scss'
})
export class AdminComponent  {

  protected selectedNav: Menu | undefined;

 //  constructor(private renderer: Renderer2) {
 //  }
 //
 // ngAfterViewInit(): void {
 //    this.loadScript('assets/vendors/ktui/ktui.min.js');
 //  }
 //
 //  loadScript(scriptUrl: string) {
 //    const script = this.renderer.createElement('script');
 //    script.src = scriptUrl;
 //    script.type = 'text/javascript';
 //    script.defer = true;
 //    script.onload = () => {};
 //    this.renderer.appendChild(document.body, script);
 //  }

  onHandelNav(nav: any) {
    this.selectedNav = nav;
  }
}
