import {Component, OnInit} from '@angular/core';
import {BkamService} from "../../../core/services/data-base/bkam/bkam.service";
import {Router} from "@angular/router";
import {PageModel} from "../../../core/models/page.model";
import {ExportHelper} from "../../../core/services/export.helper";
import {formatDate} from "@angular/common";

@Component({
  selector: 'app-indice-monia',
  standalone: false,
  templateUrl: './indice-monia.component.html',
  styleUrl: './indice-monia.component.scss'
})
export class IndiceMoniaComponent implements OnInit {
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

    this.bkamService.findIndiceMonia(filter).subscribe(response => {

      console.log("indice-monia", response)
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
    this.bkamService.findIndiceMonia(filter).subscribe(response => {
      ExportHelper.exportArrayToExcel(this.prepareDataToExport(response.content), "indice-monia");
    });
  }

  prepareDataToExport(data: Array<any>): Array<any>{
    let result = [];
    data.forEach(element => {
      result.push({
        "Date de référence": element?.dateReference
            ? formatDate(new Date(element.dateReference), 'dd/MM/yyyy', 'en-GB')
            : '',

        "Date de publication": element?.datePublication
            ? formatDate(new Date(element.datePublication), 'dd/MM/yyyy', 'en-GB')
            : '',

        "Indice MONIA": element?.indiceMonia,
        "Volume JJ": element?.volumeJj
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