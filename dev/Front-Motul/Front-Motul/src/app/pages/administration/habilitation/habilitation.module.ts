import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { HabilitationRoutingModule } from './habilitation-routing.module';
import {HabilitationDetailsComponent} from "./habilitation-details/habilitation-details.component";
import {HabilitationListComponent} from "./habilitation-list/habilitation-list.component";
import {NgbPagination} from "@ng-bootstrap/ng-bootstrap";
import {FormsModule, ReactiveFormsModule} from "@angular/forms";
import {NgLabelTemplateDirective, NgOptionTemplateDirective, NgSelectComponent} from "@ng-select/ng-select";
import {TranslatePipe} from "@ngx-translate/core";


@NgModule({
  declarations: [
      HabilitationDetailsComponent,
      HabilitationListComponent
  ],
    imports: [
        CommonModule,
        HabilitationRoutingModule,
        NgbPagination,
        FormsModule,
        ReactiveFormsModule,
        NgSelectComponent,
        TranslatePipe,
        NgOptionTemplateDirective,
        NgLabelTemplateDirective
    ]
})
export class HabilitationModule { }
