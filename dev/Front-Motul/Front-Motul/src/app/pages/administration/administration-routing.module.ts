import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
    {
        path: '',
        redirectTo: 'habilitation',
        pathMatch: 'full'
    },
    {
        path: 'habilitation',
        loadChildren: () => import('../administration/habilitation/habilitation.module').then((e) => e.HabilitationModule)
    },
    {
        path: 'historique-acces',
        loadChildren: () => import('./historique-acces/historique-acces.module').then((e) => e.HistoriqueAccesModule)
    },
    {
        path: 'utilisateurs',
        loadChildren: () =>
            import('./utilisateurs/utilisateurs.module').then((m) => m.UtilisateursModule),
    },
    {
        path: 'configuration',
        loadChildren: () =>
            import('./configuration/configuration.module').then((m) => m.ConfigurationModule),
    },

];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AdministrationRoutingModule { }
