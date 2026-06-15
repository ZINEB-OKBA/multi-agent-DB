import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {HistoriqueAccesListComponent} from "./historique-acces-list/historique-acces-list.component";

const routes: Routes = [
    {
        path: '',
        redirectTo: 'list',
        pathMatch: 'full'
    },
    {
        path: 'list',
        component: HistoriqueAccesListComponent
    },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class HistoriqueAccesRoutingModule { }
