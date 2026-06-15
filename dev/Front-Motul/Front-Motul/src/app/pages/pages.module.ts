import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { PagesRoutingModule } from './pages-routing.module';
import {LayoutModule} from '../layout/layout.module';
import { HomeComponent } from './home/home.component';
import { PageNotFoundComponent } from './page-not-found/page-not-found.component';
import {TranslatePipe} from "@ngx-translate/core";


@NgModule({
  declarations: [
    HomeComponent,
    PageNotFoundComponent
  ],
    imports: [
        CommonModule,
        LayoutModule,
        PagesRoutingModule,
        TranslatePipe,

    ]
})
export class PagesModule { }
