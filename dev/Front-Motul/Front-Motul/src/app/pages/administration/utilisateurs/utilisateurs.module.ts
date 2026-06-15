import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { UtilisateursRoutingModule } from './utilisateurs-routing.module';
import {UtilisateursListComponent} from "./utilisateurs-list/utilisateurs-list.component";
import {UtilisateursDetailsComponent} from "./utilisateurs-details/utilisateurs-details.component";
import {NgbPagination} from "@ng-bootstrap/ng-bootstrap";
import {FormsModule, ReactiveFormsModule} from "@angular/forms";
import {NgSelectComponent} from "@ng-select/ng-select";
import {TranslatePipe} from "@ngx-translate/core";
import { UtilisateurProfilComponent } from './utilisateur-profil/utilisateur-profil.component';


@NgModule({
  declarations: [
      UtilisateursListComponent,
      UtilisateursDetailsComponent,
      UtilisateurProfilComponent
  ],
    imports: [
        CommonModule,
        UtilisateursRoutingModule,
        NgbPagination,
        FormsModule,
        NgSelectComponent,
        ReactiveFormsModule,
        TranslatePipe
    ]
})
export class UtilisateursModule { }
