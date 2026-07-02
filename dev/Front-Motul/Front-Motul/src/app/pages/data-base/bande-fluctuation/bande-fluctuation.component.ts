import {Component, OnInit} from '@angular/core';
import {PageModel} from "../../../core/models/page.model";
import {ExportHelper} from "../../../core/services/export.helper";
import {BkamService} from "../../../core/services/data-base/bkam/bkam.service";
import {Router} from "@angular/router";
import {formatDate} from "@angular/common";

@Component({
  selector: 'app-bande-fluctuation',
  standalone: false,
  templateUrl: './bande-fluctuation.component.html',
  styleUrl: './bande-fluctuation.component.scss'
})
export class BandeFluctuationComponent implements OnInit {

  constructor(
      private bkamService: BkamService,
      private router: Router,
  ) {}
  protected data: any;
  protected term!: string;
  protected showAdvancedSearch : boolean = false;
  protected startDate?: string;
  protected endDate?: string;

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

    this.bkamService.findBandeFluctuation(filter).subscribe(response => {
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
    this.bkamService.findBandeFluctuation(filter).subscribe(response => {
      ExportHelper.exportArrayToExcel(this.prepareDataToExport(response.content), "bande-fluctuations");
    });
  }

  prepareDataToExport(data: Array<any>): Array<any>{
    let result = [];
    data.forEach(element => {
      result.push({
        Devise: element?.devises,
        Heure: element?.heure,

        Cours_minimum: element?.coursMinimum,
        Cours_maximum: element?.coursMaximum,
        Date : element?.scrapingDate
            ? formatDate(element.scrapingDate, 'dd-MM-yyyy', 'en-GB')
            : ''
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
