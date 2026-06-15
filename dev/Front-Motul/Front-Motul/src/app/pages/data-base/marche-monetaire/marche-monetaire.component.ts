import {Component, OnInit} from '@angular/core';
import {BkamService} from "../../../core/services/data-base/bkam/bkam.service";
import {Router} from "@angular/router";
import {PageModel} from "../../../core/models/page.model";
import {ExportHelper} from "../../../core/services/export.helper";

@Component({
  selector: 'app-marche-monetaire',
  standalone: false,
  templateUrl: './marche-monetaire.component.html',
  styleUrl: './marche-monetaire.component.scss'
})
export class MarcheMonetaireComponent implements OnInit {
  protected showAdvancedSearch: boolean = false;

  constructor(
      private bkamService: BkamService,
      private router: Router,
  ) {}
  protected data: any;
  protected term!: string;

  protected  page: PageModel = new PageModel();
  protected startDate?: string;
  protected endDate?: string;


  get currentPage(): number {
    return this.page.page + 1;
  }

  set currentPage(value: number) {
    this.page.page = value - 1;
    this.onFind();
  }
  ngOnInit(): void {
    this.onFind();
  }

  onFind() {
    const filter: any = {
      page: this.page,
      term : this.term
    };

    if (this.term) {
      filter.term = this.term;
    }

    if (this.startDate) {
      filter.startDate = this.startDate;
    }

    if (this.endDate) {
      filter.endDate = this.endDate;
    }

    this.bkamService.findMarcheMonetaire(filter).subscribe(response => {
      this.data = response;
    });
  }

  onExport() {
    const filter : any = {
      page: {page:0},
      term: this.term,
    };

    if (this.startDate) {
      filter.startDate = this.startDate;
    }

    if (this.endDate) {
      filter.endDate = this.endDate;
    }
    this.bkamService.findMarcheMonetaire(filter).subscribe(response => {
      ExportHelper.exportArrayToExcel(this.prepareDataToExport(response.content), "Marché_monétaire_interbancaire");
    });
  }

  prepareDataToExport(data: Array<any>): Array<any>{
    let result = [];
    data.forEach(element => {
      result.push({
        Date: element.date,
        Taux_moyen_pondéré: element?.tauxMoyenPondere,

        Volume_JJ: element?.volumeJj,
        Encours: element?.encours,
      });
    })
    return result;
  }

  navigate() {
    this.router.navigateByUrl('/data-base/bkam-landing', { replaceUrl: true });
    return;
  }

  handleShowAdvancedSearch(): void {
    this.showAdvancedSearch = !this.showAdvancedSearch;
  }

  resetFilters() {
    this.term = '';
    this.startDate = undefined;
    this.endDate = undefined;
    this.page.page = 0;
    this.onFind();
  }
}