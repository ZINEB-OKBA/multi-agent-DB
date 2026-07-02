import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { HistoriqueAccesRoutingModule } from './historique-acces-routing.module';
import {HistoriqueAccesListComponent} from "./historique-acces-list/historique-acces-list.component";
import {NgbPagination} from "@ng-bootstrap/ng-bootstrap";
import {FormsModule} from "@angular/forms";
import {TranslatePipe} from "@ngx-translate/core";


@NgModule({
  declarations: [
      HistoriqueAccesListComponent
  ],
    imports: [
        CommonModule,
        HistoriqueAccesRoutingModule,
        NgbPagination,
        FormsModule,
        TranslatePipe
    ]
})
export class HistoriqueAccesModule { }
