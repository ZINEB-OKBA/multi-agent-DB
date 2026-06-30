import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { StaffingComponent } from './staffing.component';

const routes: Routes = [
  {
    path: '',
    component: StaffingComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class StaffingRoutingModule { }
