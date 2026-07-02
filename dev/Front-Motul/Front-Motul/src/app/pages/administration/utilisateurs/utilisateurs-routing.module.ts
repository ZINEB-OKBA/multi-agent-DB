import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {UtilisateursListComponent} from "./utilisateurs-list/utilisateurs-list.component";
import {UtilisateursDetailsComponent} from "./utilisateurs-details/utilisateurs-details.component";
import {UtilisateurProfilComponent} from "./utilisateur-profil/utilisateur-profil.component";

const routes: Routes = [
    {
        path: '',
        redirectTo: 'list',
        pathMatch: 'full'
    },
    {
        path: 'list',
        component: UtilisateursListComponent
    },
    {
        path: 'add',
        component: UtilisateursDetailsComponent
    },
    {
        path: 'details/:id',
        component: UtilisateursDetailsComponent
    },
    {
        path: 'profile',
        component: UtilisateurProfilComponent
    }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class UtilisateursRoutingModule { }
