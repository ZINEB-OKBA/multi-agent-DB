import {Component, OnInit} from '@angular/core';
import {Router} from "@angular/router";
import {PageModel} from "../../../../core/models/page.model";
import {AlertService} from "../../../../core/auth/alert.service";
import {UserService} from "../../../../core/services/administration/users.service";

@Component({
  selector: 'app-utilisateurs-list',
  standalone: false,
  templateUrl: './utilisateurs-list.component.html',
  styleUrl: './utilisateurs-list.component.scss'
})
export class UtilisateursListComponent implements OnInit {

  constructor(
      private router: Router,
      private userService: UserService,
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
    this.userService.find(filter).subscribe(response => {
      this.data = response;
    })
  }

  onAdd() {
      this.router.navigate(['administration/utilisateurs/add']);

  }

  onEdit(id: number) {
    this.router.navigate(['administration/utilisateurs/details/', id]);
  }


  onDelete(id: number) {
    this.alertService.confirmDelete().then(result => {
      if (result.isConfirmed) {
        this.userService.delete(id).subscribe(() => {
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
