import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {HabilitationListComponent} from "./habilitation-list/habilitation-list.component";
import {HabilitationDetailsComponent} from "./habilitation-details/habilitation-details.component";

const routes: Routes = [
    {
        path: '',
        redirectTo: 'list',
        pathMatch: 'full'
    },
    {
        path: 'list',
        component: HabilitationListComponent
    },
    {
        path: 'add',
        component: HabilitationDetailsComponent
    },
    {
        path: 'details/:id',
        component: HabilitationDetailsComponent
    }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class HabilitationRoutingModule { }
