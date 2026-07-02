import { Injectable } from '@angular/core';
import Swal, { SweetAlertIcon } from 'sweetalert2';
import {TranslateService} from "@ngx-translate/core";

@Injectable({
    providedIn: 'root'
})
export class AlertService {
    constructor(private translate: TranslateService) {}


    successAlert() {
        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'success',
            title: this.translate.instant('MODULES.ALERTS.SUCCESS_TITLE'),
            text: this.translate.instant('MODULES.ALERTS.SUCCESS_MESSAGE'),
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            customClass: {
                popup: 'colored-toast'
            }
        });
    }

    error(message: string, title: string = this.translate.instant('MODULES.ALERTS.ERROR_TITLE')) {
        Swal.fire({
            icon: 'error',
            title,
            text: message,
            confirmButtonColor: '#d33'
        });
    }
    warning(message: string, title: string = this.translate.instant('MODULES.ALERTS.WARNING_TITLE')) {
        Swal.fire({
            icon: 'warning',
            title,
            text:message,
            confirmButtonColor: '#f0ad4e'
        });
    }
    confirmDelete(message: string = "Cette action est irréversible.") {
        return Swal.fire({
            title: 'Êtes-vous sûr ?',
            text: message,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#008236FF',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Oui, supprimer',
            cancelButtonText: 'Annuler'
        });
    }

}
