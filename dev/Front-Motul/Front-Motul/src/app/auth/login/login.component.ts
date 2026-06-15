import {AfterViewInit, Component, Inject, OnInit} from '@angular/core';
import {DOCUMENT} from '@angular/common';
import {FormBuilder, FormGroup, Validators} from '@angular/forms';
import {Router} from '@angular/router';
import {AuthenticationService} from '../../core/auth/authentication.service';
import {SessionStorageService} from '../../core/auth/session.storage.service';
import {ExceptionsEnum} from "../../core/enums/exceptions.enum";

@Component({
  standalone: false,
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent implements OnInit, AfterViewInit {

  protected form: FormGroup;
  protected error : any;
  protected readonly ExceptionsEnum = ExceptionsEnum;

  constructor(
    @Inject(DOCUMENT) private document: Document,
    private formBuilder: FormBuilder,
    private session: SessionStorageService,
    private router: Router,
    private authenticationService: AuthenticationService
    ) {
  }

  ngOnInit(): void {
    this.initForm();
  }

  initForm() {
    this.form = this.formBuilder.group({
      email: ['admin@gmail.com', Validators.required],
      password: ['admin', Validators.required]
    });
  }

  onSubmit() {
    this.authenticationService.attemptAuthentication(this.form.value).subscribe(
      data => {
        this.session.setUser(data);
        this.router.navigate(['/assistant-conversationnel/chat']);
      },
      error => {
        this.setLoginErrorMessage(error);
      }
    )
    this.router.navigate(['/assistant-conversationnel/chat']);
  }

  setLoginErrorMessage(ex: any) {
    this.error = ex.error?.reason
  }


  ngAfterViewInit(): void {
    this.document.body.classList.add('antialiased');
    this.document.body.classList.add('h-full');
    this.document.body.classList.add('text-base');
    this.document.body.classList.add('text-foreground');
    this.document.body.classList.add('bg-background');
  }

}
