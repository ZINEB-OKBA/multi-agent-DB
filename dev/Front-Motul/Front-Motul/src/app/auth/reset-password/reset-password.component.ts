import {Component, OnInit} from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {AlertService} from "../../core/auth/alert.service";
import {AuthenticationService} from "../../core/auth/authentication.service";
import {AbstractControl, FormBuilder, FormGroup, ValidationErrors, ValidatorFn, Validators} from "@angular/forms";

@Component({
  standalone: false,
  selector: 'app-reset-password',
  templateUrl: './reset-password.component.html',
  styleUrl: './reset-password.component.scss'
})
export class ResetPasswordComponent  implements OnInit{
  protected   form : FormGroup;
  protected   submitted  : boolean = false;
  protected   loading   : boolean = false;
  protected   error     : any;


  constructor(
      private router: Router,
      private alertService: AlertService,
      private formBuilder: FormBuilder,
      private activatedRoute: ActivatedRoute,
      private authService: AuthenticationService,
  ){
  }


  ngOnInit(): void {

    this.initForm();
    this.onLoadSercret();
  }

  protected initForm(){
    this.form = this.formBuilder.group(
        {
          secret: [null, Validators.required],
          newPassword: [null, [Validators.required, Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$/)]],
          password: [null, [Validators.required]]
        },
        { validators: this.passwordMatchValidator() }
    );
  }
  get formValues() {
    return this.form.controls;
  }

  protected onSubmit() {
    this.submitted = true;
    this.loading = true;
    // stop here if form is invalid
    if (this.form.invalid) {
      this.loading = false;
      return;
    }

    this.authService.setNewPassword(this.form?.value).subscribe({
      next: (response) => {
        if (response) {
          this.alertService.successAlert();
           this.router.navigate(["/auth/login"])
        }
      },
      error: error => {
        console.error('Error setting new password:', error);
        this.loading = false;
      }
    })
  }
  private passwordMatchValidator(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const password = control.get('newPassword')?.value;
      const confirmPassword = control.get('password')?.value;

      return password && confirmPassword && password !== confirmPassword
          ? { passwordMismatch: true }
          : null;
    };
  }

  protected onLoadSercret(){
    this.activatedRoute.params.subscribe(params => {
      const secret = params['secret'];
      this.form?.get('secret')?.setValue(secret);
    });
  }
  isFieldInvalid(field: string): boolean {
    const control = this.form.get(field);
    return !!(control && control.invalid && (control.dirty || this.submitted));
  }

}
