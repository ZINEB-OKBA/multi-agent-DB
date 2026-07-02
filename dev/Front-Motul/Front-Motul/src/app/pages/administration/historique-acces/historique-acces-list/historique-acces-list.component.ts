import {Component, OnInit} from '@angular/core';
import {Router} from "@angular/router";
import {AlertService} from "../../../../core/auth/alert.service";
import {PageModel} from "../../../../core/models/page.model";
import {AttemptAuthenticationsService} from "../../../../core/services/audit/attempt.authentications.service";

@Component({
  selector: 'app-historique-acces-list',
  standalone: false,
  templateUrl: './historique-acces-list.component.html',
  styleUrl: './historique-acces-list.component.scss'
})
export class HistoriqueAccesListComponent implements OnInit {

  constructor(
      private router: Router,
      private attemptAuthentications: AttemptAuthenticationsService,
      private alertService: AlertService,
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
    let filter = {
      page: this.page,
      term: this.term,
    };
    this.attemptAuthentications.find(filter).subscribe(response => {
      this.data = response;
    })
  }

  onSort(column: string) {
    this.page.column = column;
    this.page.direction = this.page.direction === 'ASC' ? 'DESC' : 'ASC';
    this.page.sortable = true;
    this.onFind();
  }
}