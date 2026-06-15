import {Component, OnInit} from '@angular/core';
import {FormBuilder, FormGroup, Validators} from "@angular/forms";
import {ActivatedRoute, Router} from "@angular/router";
import {PageModel} from "../../../../core/models/page.model";
import {UserService} from "../../../../core/services/administration/users.service";
import {ProfilesService} from "../../../../core/services/administration/profiles.service";
import {AlertService} from "../../../../core/auth/alert.service";

@Component({
  selector: 'app-utilisateurs-details',
  standalone: false,
  templateUrl: './utilisateurs-details.component.html',
  styleUrl: './utilisateurs-details.component.scss'
})
export class UtilisateursDetailsComponent implements  OnInit {

  protected submitted!: boolean;
  protected form!: FormGroup;
  protected page = new PageModel();
  protected profileList: Array<any> | undefined;
  protected airportList: Array<any> | undefined;


  constructor(
      private fb: FormBuilder,
      private activatedRoute: ActivatedRoute,
      private userService: UserService,
      private profilesService: ProfilesService,
      private router: Router,
      private alertService: AlertService,
) {}

  ngOnInit(): void {
    this.initForm();
    this.initElement();
    this.loadProfiles();
  }

  private loadProfiles() {
    const filter = {
      page: {page: 0},
    }
    this.profilesService.find(filter).subscribe(response => {
      this.profileList = response?.content;
    })
  }


  private initForm() {
    this.form = this.fb.group({
      id: [null],
      firstName: [null, [Validators.required, Validators.pattern('^[^><\"`]*$')]],
      lastName: [null, [Validators.required, Validators.pattern('^[^><\"`]*$')]],
      email: ['', [Validators.required, Validators.email]],
      phone: [null, [Validators.required]],
      profile:  [null, [Validators.required]],
      enabled: [null, [Validators.required]],
    });
  }

  initElement() {
    this.activatedRoute.params.subscribe(params => {
      const id = params['id'];
      if (id) {
        this.userService.get(id).subscribe(response => {
          this.form.patchValue(response);
        });
      }
    });
  }

  onSubmit() {
    this.submitted = true;

    if (this.form.valid) {
      this.userService.save(this.form.value).subscribe({
        next: (data) => {
          this.alertService.successAlert();
          this.router.navigate(['/administration/utilisateurs/list']);
        },
        error: (ex) => {
          if (ex.error?.reason == 'USER-EXIST') {
            this.alertService.warning('Nom d\'utilisateur déjà existant !')
          }
        },
      });

    }
  }

  onCancel(): void {
    this.form.reset();
    this.router.navigate(['/administration/utilisateurs/list']);
  }

  isFieldInvalid(field: string): boolean {
    const control = this.form.get(field);
    return !!(control && control.invalid && (control.dirty || this.submitted));
  }
  compareFn(t1: any, t2: any): boolean {
    return t1 && t2 ? t1.id === t2.id : t1 === t2;
  }

}
