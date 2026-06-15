import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { LayoutRoutingModule } from './layout-routing.module';
import {AdminComponent} from './admin/admin.component';
import {EmptyComponent} from './empty/empty.component';
import {HeaderComponent} from './header/header.component';
import {SidebarComponent} from './sidebar/sidebar.component';
import {NavbarComponent} from './navbar/navbar.component';
import {FooterComponent} from './footer/footer.component';
import {TranslatePipe} from "@ngx-translate/core";


@NgModule({
  declarations: [
    AdminComponent,
    EmptyComponent,
    HeaderComponent,
    SidebarComponent,
    NavbarComponent
  ],
    imports: [
        CommonModule,
        LayoutRoutingModule,
        FooterComponent,
        TranslatePipe
    ]
})
export class LayoutModule { }
