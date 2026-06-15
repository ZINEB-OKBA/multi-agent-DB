import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';
import {Menu, NavService} from '../../core/menu/nav.service';
import {SessionStorageService} from "../../core/auth/session.storage.service";
import {RoleEnum} from "../../core/enums/role.enum";
import {Router} from "@angular/router";

@Component({
    standalone: false,
    selector: 'app-navbar',
    templateUrl: './navbar.component.html',
    styleUrl: './navbar.component.scss'
})
export class NavbarComponent implements OnInit, OnChanges {

    @Input() nav: Menu | undefined;
    protected authorities: Array<RoleEnum> = [];


    protected isDisplayActionButtons: boolean;


    constructor(
        private router: Router,
        private sessionStorageService: SessionStorageService,
    ) {
        this.authorities = this.sessionStorageService.getAuthority();
    }

    ngOnInit() {
    }

    onParentClick(item: Menu, event: MouseEvent) {
        event.stopPropagation();
        if (item.path) {
            this.router.navigate([item.path]);
        }
    }
    ngOnChanges(changes: SimpleChanges) {
        if ((changes['nav']?.currentValue?.path != changes['nav']?.previousValue?.path) && changes['nav']?.previousValue){
            if (this.nav && this.nav.children && this.nav.children.length > 0 ) {
                this.router.navigate([this.nav.children[0].path]);
            }
        }
    }

    protected hasAuthorities(roles: Array<RoleEnum>): boolean {
        if (roles?.length <= 0){
            return true;
        }
        for (let i in roles) {
            if (this.authorities.indexOf(roles[i]) > -1) {
                return true;
            }
        }
        return false;
    }
}
