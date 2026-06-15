import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './login/login.component';
import {ForgotPasswordComponent} from "./forgot-password/forgot-password.component";
import {ResetPasswordComponent} from "./reset-password/reset-password.component";

const routes: Routes = [
      {
          path: '',
          redirectTo: 'login',
          pathMatch: 'full'
      },
      {
          path: 'login',
          component: LoginComponent
      },
    {
        path: 'new-password/:secret',
        component: ResetPasswordComponent,
    },
    {
        path: 'forgot-password',
        component: ForgotPasswordComponent,
    }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AuthRoutingModule { }
