import {Component, OnInit} from '@angular/core';
import {BkamService} from "../../../core/services/data-base/bkam/bkam.service";
import {Router} from "@angular/router";
import {PageModel} from "../../../core/models/page.model";
import {ExportHelper} from "../../../core/services/export.helper";
import {InstrumentTypeEnum} from "../../../core/enums/instrument.type.enum";
import {formatDate} from "@angular/common";

@Component({
  selector: 'app-operations-principales',
  standalone: false,
  templateUrl: './operations-principales.component.html',
  styleUrl: './operations-principales.component.scss'
})
export class OperationsPrincipalesComponent implements OnInit {

  constructor(
      private bkamService: BkamService,
      private router: Router,
  ) {}
  protected data: any;
  protected term!: string;
  protected showAdvancedSearch : boolean = false;
  protected startDate?: string;
  protected endDate?: string;
  instrumentOptions = Object.values(InstrumentTypeEnum);
  selectedInstrument!: InstrumentTypeEnum;

  protected  page: PageModel = new PageModel();


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

    if (this.selectedInstrument) {
      filter.instrument = this.selectedInstrument;
    }

    this.bkamService.findOperationsPrincipales(filter).subscribe(response => {
      console.log("Operations principales ", response);
      this.data = response;
    });
  }

  onExport() {
    let filter : any = {
      page: {page:0},
      term: this.term
    };

    if (this.startDate) {
      filter.startDate = this.startDate;
    }

    if (this.endDate) {
      filter.endDate = this.endDate;
    }

    if (this.selectedInstrument) {
      filter.instrument = this.selectedInstrument;
    }
    this.bkamService.findOperationsPrincipales(filter).subscribe(response => {
      ExportHelper.exportArrayToExcel(this.prepareDataToExport(response.content), "operations-principales");
    });
  }

  prepareDataToExport(data: Array<any>): Array<any>{
    let result = [];
    data.forEach(element => {
      result.push({
        "Date appel d’offres": element?.dateAppelOffres
            ? formatDate(element.dateAppelOffres, 'dd-MM-yyyy', 'en-GB')
            : '',
        "Date de valeur": element?.dateDeValeur
            ? formatDate(element.dateDeValeur, 'dd-MM-yyyy', 'en-GB')
            : '',
        "Date échéance": element?.dateEcheance
            ? formatDate(element.dateEcheance, 'dd-MM-yyyy', 'en-GB')
            : '',
        "Instrument": element?.instrument,
        "Montant demandé": element?.montantDemande,
        "Montant servi": element?.montantServi,
        "Taux": element?.taux
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
    this.selectedInstrument = undefined;
    this.page.page = 0;
    this.onFind();
  }
}

