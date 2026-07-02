import {Component, OnInit} from '@angular/core';
import {Router} from "@angular/router";
import {PageModel} from "../../../core/models/page.model";
import {AmmcService} from "../../../core/services/data-base/ammc/ammc.service";

@Component({
  selector: 'app-ammc',
  standalone: false,
  templateUrl: './ammc.component.html',
  styleUrl: './ammc.component.scss'
})
export class AmmcComponent implements OnInit {

  constructor(
      private router: Router,
      private ammcService: AmmcService,
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
    };
    this.ammcService.find(filter).subscribe((response) =>{
      this.data = response;
    })
  }

  navigate() {
    this.router.navigateByUrl('/data-base', { replaceUrl: true });
    return;
  }
}