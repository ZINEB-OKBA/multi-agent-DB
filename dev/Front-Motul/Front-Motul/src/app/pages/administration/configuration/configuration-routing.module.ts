import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {EmailNotificationComponent} from "./email-notification/email-notification.component";

const routes: Routes = [
  {
    path: '',
    redirectTo: 'email-notifications',
    pathMatch: 'full'
  },
  {
    path: 'email-notifications',
    component: EmailNotificationComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ConfigurationRoutingModule { }
