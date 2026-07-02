import {Component, OnInit} from '@angular/core';
import {Router} from "@angular/router";
import {ProfilesService} from "../../../../core/services/administration/profiles.service";
import {AlertService} from "../../../../core/auth/alert.service";
import {PageModel} from "../../../../core/models/page.model";

@Component({
  selector: 'app-habilitation-list',
  standalone: false,
  templateUrl: './habilitation-list.component.html',
  styleUrl: './habilitation-list.component.scss'
})
export class HabilitationListComponent implements OnInit {
  constructor(
      private router: Router,
      private profileService: ProfilesService,
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
    this.profileService.find(filter).subscribe(response => {
      this.data = response;
    })
  }

  onAdd() {
    this.router.navigate(['administration/habilitation/add']);
  }

  onEdit(id: number) {
    this.router.navigate(['administration/habilitation/details/' + id]);
  }

  onDelete(id: number) {
    this.alertService.confirmDelete().then(result => {
      if (result.isConfirmed) {
        this.profileService.delete(id).subscribe(() => {
          this.onFind();
          this.alertService.successAlert();
        });
      }
    });
  }

  onSort(column: string) {
    this.page.column = column;
    this.page.direction = this.page.direction === 'ASC' ? 'DESC' : 'ASC';
    this.page.sortable = true;
    this.onFind();
  }

}
