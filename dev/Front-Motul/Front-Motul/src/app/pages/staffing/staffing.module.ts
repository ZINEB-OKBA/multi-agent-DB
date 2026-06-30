import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StaffingComponent } from './staffing.component';
import { StaffingRoutingModule } from './staffing-routing.module';
import { TranslateModule } from '@ngx-translate/core';
import { FormsModule } from '@angular/forms';

@NgModule({
  declarations: [
    StaffingComponent
  ],
  imports: [
    CommonModule,
    StaffingRoutingModule,
    TranslateModule,
    FormsModule
  ]
})
export class StaffingModule { }
