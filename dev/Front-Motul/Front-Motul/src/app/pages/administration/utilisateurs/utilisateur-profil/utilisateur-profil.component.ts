import {Component, OnInit} from '@angular/core';
import {FormBuilder, FormGroup, Validators} from "@angular/forms";
import {PageModel} from "../../../../core/models/page.model";
import {ActivatedRoute, Router} from "@angular/router";
import {UserService} from "../../../../core/services/administration/users.service";
import {AlertService} from "../../../../core/auth/alert.service";
import {AuthenticationService} from "../../../../core/auth/authentication.service";
import {TranslateService} from "@ngx-translate/core";

@Component({
  selector: 'app-utilisateur-profil',
  standalone: false,
  templateUrl: './utilisateur-profil.component.html',
  styleUrl: './utilisateur-profil.component.scss'
})
export class UtilisateurProfilComponent implements OnInit {

  protected submitted!: boolean;
  protected profileForm!: FormGroup;
  protected passwordForm!: FormGroup;
  protected userId!: string;
  protected page = new PageModel();
  public image: string | ArrayBuffer | null = null;
  protected passwordMismatch: boolean;


  constructor(
      private fb: FormBuilder,
      private userService: UserService,
      private router: Router,
      private alertService: AlertService,
      private authenticationService: AuthenticationService,
      private translate: TranslateService,
  ) {
  }

  ngOnInit(): void {
    this.initForm();
    this.initElement();
  }


  private initForm() {
    this.profileForm = this.fb.group({
      id: [null],
      lastName: [null, [Validators.required, Validators.pattern('^[^><\"`]*$')]],
      firstName: [null, [Validators.required, Validators.pattern('^[^><\"`]*$')]],
      email: ['', [Validators.required, Validators.email]],
      phone: [null, [Validators.required, Validators.pattern(/^\d{10}$/)]],
      image: [null],
      enabled : [null]

    });
    this.passwordForm = this.fb.group({
      password: ['', Validators.required],
      newPassword: ['', [Validators.required, Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$/)]],
      confirmPassword: ['', [Validators.required, Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$/)]],
    });
  }

  initElement() {
    this.userId = JSON.parse(sessionStorage.getItem('user'))?.id;
    if (this.userId) {
      this.userService.get(this.userId).subscribe(response => {
        this.profileForm.patchValue(response);

        if (response?.image) {
          this.image = 'data:image/jpeg;base64,' + response.image;
        } else {
          this.image = null;
        }
      });
    }
  }


  onSubmitUpdateProfile() {
    this.submitted = true;

    if (this.profileForm.valid) {
      this.userService.save(this.profileForm.value).subscribe({
        next: (data) => {
          this.alertService.successAlert();
          this.router.navigate(['/']);
        }
      });

    }
  }

  onCancelProfileForm(): void {
    this.profileForm.reset();
    this.router.navigate(['/']);
  }

  isProfileFormFieldInvalid(field: string): boolean {
    const control = this.profileForm.get(field);
    return !!(control && control.invalid && (control.dirty || this.submitted));
  }

  isPasswordFormFieldInvalid(field: string): boolean {
    const control = this.passwordForm.get(field);
    return !!(control && control.invalid && (control.dirty || this.submitted));
  }

  get passwordFormValues() {
    return this.passwordForm.controls;
  }

  protected onFileChange(event: any): void {
    const reader = new FileReader();
    const input = event.target as HTMLInputElement;

    if (input.files && input.files.length) {
      const file = input.files[0];
      const maximalImageSize = JSON.parse(sessionStorage.getItem("user"))?.maxUpload;

      if (file.size > maximalImageSize) {
        this.alertService.warning(this.translate.instant('MODULES.PROFILES.ALERTS.IMAGE_TOO_LARGE') + (maximalImageSize/1000000) + "MB", this.translate.instant('MODULES.PROFILES.ALERTS.TITLE'));
        input.value = '';
        return;
      }

      if (!['image/jpeg', 'image/png', 'image/jpg'].includes(file.type)) {
        this.alertService.warning(this.translate.instant('MODULES.PROFILES.ALERTS.INVALID_FORMAT') + (maximalImageSize/1000000) + "MB", this.translate.instant('MODULES.PROFILES.ALERTS.TITLE'));
        input.value = '';
        return;
      }

      reader.onload = () => {
        if (typeof reader.result === 'string') {
          this.image = reader.result;
          this.profileForm.patchValue({
            image: reader.result.split(',')[1]
          });
        }
      };
      reader.readAsDataURL(file);
    }

    input.value = '';
  }

  onPasswordSubmit() {
    if (!(this.passwordForm.value.newPassword == this.passwordForm.value.confirmPassword)){
      this.passwordMismatch = true;
      return;
    }
    if (this.passwordForm.valid) {
      const body = {
        id : this.userId,
        password : this.passwordForm.value.password,
        newPassword : this.passwordForm.value.newPassword,
      }

      this.authenticationService.updatePassword(body).subscribe({
        next:(response) => {
          if (response){
            this.alertService.successAlert();
            this.router.navigate(['/']);
          }
        },
        error:(err)=> {
          this.alertService.warning(this.translate.instant('MODULES.ALERTS.' + err?.error?.reason));
        }
      });

    }
  }

  onCancelPasswordForm() {
    this.passwordForm.reset();
    this.router.navigate(['/']);
  }


  removeProfilePhoto() {
    this.image = null;
    this.profileForm.patchValue({
      image: null
    });
  }
}


