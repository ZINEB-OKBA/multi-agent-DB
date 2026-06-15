import { Component, OnInit } from '@angular/core';
import { AlertService } from "../../../../core/auth/alert.service";
import { EmailNotificationConfigService } from "../../../../core/services/administration/config.service";

@Component({
  selector: 'app-email-notification',
  standalone: false,
  templateUrl: './email-notification.component.html',
  styleUrl: './email-notification.component.scss'
})
export class EmailNotificationComponent implements OnInit {

  data: any[] = [];
  isSubmitting = false;

  constructor(
      private alertService: AlertService,
      private emailNotificationConfigService: EmailNotificationConfigService,
  ) {
  }

  ngOnInit() {
    this.loadConfig();
  }

  loadConfig(): void {
    this.emailNotificationConfigService.find().subscribe({
      next: (response) => {
        this.data = response;
      }
    });
  }

  onCheckboxChange(row: any, field: string, event: any) {
    row[field] = event.target.checked;
  }

  onSubmit(): void {
    this.isSubmitting = true;
    this.emailNotificationConfigService.save(this.data).subscribe(response =>{
        this.isSubmitting = false;
        this.alertService.successAlert();
    });
  }
}