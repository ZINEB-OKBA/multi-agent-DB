import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { ListSourceDataComponent } from './list-source-data/list-source-data.component';
import { DocumentsListComponent } from './document-list/document-list.component';
import { AmmcComponent } from './ammc/ammc.component';
import { ProjectLandingComponent } from './project-landing/project-landing.component';
import { ProjectsListComponent } from './project-list/project-list.component';
import { BkamLandingComponent } from './bkam-landing/bkam-landing.component';
import { BandeFluctuationComponent } from './bande-fluctuation/bande-fluctuation.component';
import { CoursBilletsComponent } from './cours-billets/cours-billets.component';
import { HistoriqueDecisionComponent } from './historique-decision/historique-decision.component';
import { IndiceMoniaComponent } from './indice-monia/indice-monia.component';
import { MarcheMonetaireComponent } from './marche-monetaire/marche-monetaire.component';
import { OperationsPrincipalesComponent } from './operations-principales/operations-principales.component';
import { ReferenceRatesComponent } from './reference-rates/reference-rates.component';

const routes: Routes = [
  {
    path: '',
    component: ProjectsListComponent
  },
  // ── 📁 NOUVEAU BLOC PROJETS SYNCHRONISÉ ────────────────────────────────
  {
    path: 'projects',
    children: [
      {
        path: '',
        component: ProjectsListComponent // Charge le 2ème HTML (Grille des projets)
      },
      {
        path: ':id',
        component: ProjectLandingComponent // Charge le 3ème HTML (Choix PDF / Excel)
      },
      {
        path: ':id/documents',
        component: DocumentsListComponent // Charge le 1er HTML (Tableau des fichiers)
      }
    ]
  },
  // ── 🏦 SOURCES BANQUE AL-MAGHRIB & AMMC ───────────────────────────────
  { path: 'bkam-landing', component: BkamLandingComponent },
  { path: 'bande-fluctuation', component: BandeFluctuationComponent },
  { path: 'cours-billet', component: CoursBilletsComponent },
  { path: 'historique-decision', component: HistoriqueDecisionComponent },
  { path: 'indice-monia', component: IndiceMoniaComponent },
  { path: 'marche-monetaire', component: MarcheMonetaireComponent },
  { path: 'operations-principales', component: OperationsPrincipalesComponent },
  { path: 'reference-rates', component: ReferenceRatesComponent },
  { path: 'ammc', component: AmmcComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class DataBaseRoutingModule { }