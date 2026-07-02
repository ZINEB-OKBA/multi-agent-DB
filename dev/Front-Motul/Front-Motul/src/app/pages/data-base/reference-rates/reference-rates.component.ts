import {Component, OnInit} from '@angular/core';
import {BkamService} from "../../../core/services/data-base/bkam/bkam.service";
import {Router} from "@angular/router";
import {PageModel} from "../../../core/models/page.model";
import {ExportHelper} from "../../../core/services/export.helper";
import {formatDate} from "@angular/common";

@Component({
  selector: 'app-reference-rates',
  standalone: false,
  templateUrl: './reference-rates.component.html',
  styleUrl: './reference-rates.component.scss'
})
export class ReferenceRatesComponent implements OnInit {

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

    this.bkamService.findReferenceRate(filter).subscribe(response => {
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
    this.bkamService.findReferenceRate(filter).subscribe(response => {
      ExportHelper.exportArrayToExcel(this.prepareDataToExport(response.content), "Reference-rates");
    });
  }

  prepareDataToExport(data: Array<any>): Array<any>{
    let result = [];
    data.forEach(element => {
      result.push({
        Devise : element?.devise,
        Cours_moyen : element?.moyen,
        Date:element?.date
            ? formatDate(element.date, 'dd-MM-yyyy', 'en-GB')
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

