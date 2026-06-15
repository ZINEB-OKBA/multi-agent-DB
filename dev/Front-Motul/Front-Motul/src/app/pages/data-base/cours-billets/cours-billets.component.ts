import {Component, OnInit} from '@angular/core';
import {BkamService} from "../../../core/services/data-base/bkam/bkam.service";
import {PageModel} from "../../../core/models/page.model";
import {ExportHelper} from "../../../core/services/export.helper";
import {Router} from "@angular/router";

@Component({
  selector: 'app-cours-billets',
  standalone: false,
  templateUrl: './cours-billets.component.html',
  styleUrl: './cours-billets.component.scss'
})
export class CoursBilletsComponent implements OnInit {

  constructor(
      private bkamService: BkamService,
      private router: Router,
  ) {}
  protected data: any;
  protected term!: string;

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

    this.bkamService.findCoursBillets(filter).subscribe(response => {
      this.data = response;
    });
  }

  onExport() {
    let filter = {
      page: {page:0},
      term: this.term
    };
    this.bkamService.findCoursBillets(filter).subscribe(response => {
      ExportHelper.exportArrayToExcel(this.prepareDataToExport(response.content), "cours-billets");
    });
  }

  prepareDataToExport(data: Array<any>): Array<any>{
    let result = [];
    data.forEach(element => {
      result.push({
        Devise: element?.devises,
        Achat_clientèle: element?.achatClientele,
        Vente_clientèle: element?.venteClientele,
      });
    })
    return result;
  }

  navigate() {
      this.router.navigateByUrl('/data-base/bkam-landing', { replaceUrl: true });
      return;
  }
}
