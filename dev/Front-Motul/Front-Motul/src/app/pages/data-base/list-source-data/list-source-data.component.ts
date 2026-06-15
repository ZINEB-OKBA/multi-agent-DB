import {Component, OnInit} from '@angular/core';
import {Router} from "@angular/router";
import {AsfimService} from "../../../core/services/data-base/asfim/asfim.service";
import {PageModel} from "../../../core/models/page.model";

@Component({
  selector: 'app-list-source-data',
  standalone: false,
  templateUrl: './list-source-data.component.html',
  styleUrl: './list-source-data.component.scss'
})
export class ListSourceDataComponent implements OnInit{

  constructor(
      private router: Router,
  ) {
  }

  ngOnInit(): void {

    }

  navigate(toComponent: string) {
    this.router.navigateByUrl(`/data-base/${toComponent}`);
  }


}
