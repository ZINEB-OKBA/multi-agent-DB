import {Component, OnInit} from '@angular/core';
import {FormBuilder, FormGroup, Validators} from "@angular/forms";
import {ActivatedRoute, Router} from "@angular/router";
import {AlertService} from "../../../../core/auth/alert.service";
import {ProfilesService} from "../../../../core/services/administration/profiles.service";

@Component({
  selector: 'app-habilitation-details',
  standalone: false,
  templateUrl: './habilitation-details.component.html',
  styleUrl: './habilitation-details.component.scss'
})
export class HabilitationDetailsComponent implements  OnInit {
  form!: FormGroup;
  submitted = false;
  modulesList: any;
  rolesList: any;

  protected  role: any;
  protected  module: any;


  constructor(
      private formBuilder: FormBuilder,
      private activatedRoute: ActivatedRoute,
      private router: Router,
      private alertService: AlertService,
      private profileService: ProfilesService,
  ) {}

  ngOnInit(): void {
    this.initForm();
    this.initElement();
    this.loadModules();
  }

  loadModules() {
    this.profileService.getModules().subscribe(response => {
      this.modulesList = response;
    });
  }

  loadRoles(module: any) {
    this.profileService.getRoles(module).subscribe(response => {
      this.rolesList = response;
    });
  }

  private initForm() {
    this.form = this.formBuilder.group({
      id: [null],
      roles: [[]],
      name: [null, [Validators.required]],
    });
  }

  initElement() {
    this.activatedRoute.params.subscribe(params => {
      const id = params['id'];
      if (id) {
        this.profileService.get(id).subscribe(response => {
          this.form.patchValue(response);
        });
      }
    });
  }

  onAddRole() {
    let exist = false;
    let affectedRoles = [...this.form.value.roles];
    affectedRoles.forEach(element => {
      if(element.identifiant == this.role.identifiant){
        this.alertService.error("Role axiste déja !")
        exist = true;
      }
    });

    if(!exist){
      affectedRoles.push(this.role);
      this.form.controls["roles"].setValue(affectedRoles);
      this.role = undefined;
    }
  }

  onDelete(element: any) {
    let affectedRoles = [...this.form.value.roles];
    const index = affectedRoles.indexOf(element, 0);

    if (index > -1) {
      affectedRoles.splice(index, 1);
      this.form.controls["roles"].setValue(affectedRoles);
    }
  }

  onSubmit(): void {
    this.submitted = true;
    if (this.form.valid) {
      this.profileService.save(this.form.value).subscribe((re) => {
        this.submitted = false;
        this.alertService.successAlert();
        this.router.navigate(['/administration/habilitation/list']);
      });
    }
  }

  onCancel(): void {
    this.form.reset();
    this.router.navigate(['/administration/habilitation/list']);
  }

  isFieldInvalid(field: string): boolean {
    const control = this.form.get(field);
    return !!(control && control.invalid && (control.dirty || this.submitted));
  }
}
