import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ConfigurationRoutingModule } from './configuration-routing.module';
import { EmailNotificationComponent } from './email-notification/email-notification.component';
import {FormsModule, ReactiveFormsModule} from "@angular/forms";
import {TranslatePipe} from "@ngx-translate/core";


@NgModule({
  declarations: [
    EmailNotificationComponent
  ],
  imports: [
    CommonModule,
    ConfigurationRoutingModule,
    ReactiveFormsModule,
    TranslatePipe,
    FormsModule
  ]
})
export class ConfigurationModule { }
