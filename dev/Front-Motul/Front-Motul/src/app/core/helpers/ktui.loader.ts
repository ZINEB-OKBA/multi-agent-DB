
import { Injectable, Renderer2, RendererFactory2 } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class KtuiLoader {
  private renderer: Renderer2;

  constructor(private rendererFactory: RendererFactory2) {
    this.renderer = rendererFactory.createRenderer(null, null);
  }


  loadScript(scriptUrl: string) {
    const script = this.renderer.createElement('script');
    script.src = scriptUrl;
    script.type = 'text/javascript';
    script.defer = true;
    script.onload = () => {};
    this.renderer.appendChild(document.body, script);
  }


  initKtui(): void {
    this.loadScript('assets/vendors/ktui/ktui.min.js');
  }
}
