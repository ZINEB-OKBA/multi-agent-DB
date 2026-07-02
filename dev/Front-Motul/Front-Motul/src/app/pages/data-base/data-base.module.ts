import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common'; // Indispensable pour | date, | number, ngClass, ngStyle
import { FormsModule } from '@angular/forms';     // Indispensable pour [(ngModel)]
import { RouterModule } from '@angular/router';

// 📦 Modules Tierces (Third-party) à ajouter pour corriger les erreurs HTML
import { TranslateModule } from '@ngx-translate/core';             // Enlève l'erreur "No pipe found with name 'translate'"
import { NgbPaginationModule } from '@ng-bootstrap/ng-bootstrap'; // Enlève l'erreur "'ngb-pagination' is not a known element"
import { NgSelectModule } from '@ng-select/ng-select';             // Enlève l'erreur "'ng-select' is not a known element"

// 🧭 Routage local
import { DataBaseRoutingModule } from './data-base-routing.module';

// 📝 Déclaration de TOUS tes composants locaux
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

@NgModule({
    declarations: [
        ListSourceDataComponent,
        DocumentsListComponent,
        AmmcComponent,
        ProjectLandingComponent,
        ProjectsListComponent,
        BkamLandingComponent,
        BandeFluctuationComponent,
        CoursBilletsComponent,
        HistoriqueDecisionComponent,
        IndiceMoniaComponent,
        MarcheMonetaireComponent,
        OperationsPrincipalesComponent,
        ReferenceRatesComponent
    ],
    imports: [
        CommonModule,         // Partage les pipes natifs (date, number, percent) et directives structurelles
        FormsModule,          // Partage l'infrastructure des formulaires pour [(ngModel)]
        DataBaseRoutingModule,
        TranslateModule,      // Rend le pipe '| translate' disponible dans tous les templates listés ci-dessus
        NgbPaginationModule,  // Rend la pagination Bootstrap exploitable
        NgSelectModule        // Rend le composant de sélection avancée exploitable
    ]
})
export class DataBaseModule { }