import {Component, OnInit} from '@angular/core';
import {FormBuilder, FormGroup, Validators} from "@angular/forms";
import {AlertService} from "../../core/auth/alert.service";
import {AuthenticationService} from "../../core/auth/authentication.service";
import {Router} from "@angular/router";

@Component({
  standalone: false,
  selector: 'app-forgot-password',
  templateUrl: './forgot-password.component.html',
  styleUrl: './forgot-password.component.scss'
})
export class ForgotPasswordComponent implements OnInit {

  protected form!: FormGroup;

  constructor(
      private fb: FormBuilder,
      private alertService: AlertService,
      private authenticationService: AuthenticationService,
      private router: Router,
  ) {}

  ngOnInit(): void {
    this.initForm();
  }

  private initForm() {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
    });
  }

  onSubmit(){
    if (!this.form.invalid){
      this.authenticationService.forgotPassword(this.form.get('email').value).subscribe(response =>{
        if (response){
          this.alertService.successAlert();
          this.router.navigate(['/login']);
        }else {
          this.alertService.warning("Tentatives maximales atteintes. Votre compte est maintenant bloqué.")
        }
      })
    }
  }

  protected readonly onsubmit = onsubmit;




}
