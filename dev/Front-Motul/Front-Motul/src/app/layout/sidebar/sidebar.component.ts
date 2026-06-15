import {Component, EventEmitter, OnInit, Output} from '@angular/core';
import {Menu, NavService} from '../../core/menu/nav.service';
import {Router} from "@angular/router";
import {RoleEnum} from "../../core/enums/role.enum";
import {SessionStorageService} from "../../core/auth/session.storage.service";
import {identity} from "rxjs";

@Component({
    standalone: false,
    selector: 'app-sidebar',
    templateUrl: './sidebar.component.html',
    styleUrl: './sidebar.component.scss'
})
export class SidebarComponent implements OnInit {


    @Output() nav = new EventEmitter<Menu>();

    protected items: Menu[] | undefined;
    protected authorities: Array<RoleEnum> = [];

    constructor(
        private sessionStorageService: SessionStorageService,
        private navService: NavService,
        private router: Router
    ) {
        this.authorities = this.sessionStorageService.getAuthority();
    }

    ngOnInit() {
        this.navService.items.subscribe(items => {
            this.items = items;
            this.setDefaultNav();
        });
    }
    onSidebarClick(item: Menu, event: MouseEvent) {
        event.preventDefault();
        event.stopPropagation();

        this.onLoadNav(item);

        if (item.path) {
            this.router.navigate([item.path]);
        }
    }

    onLoadNav(nav: Menu) {
        this.nav.emit(nav);
    }

    setDefaultNav() {
        let path = this.router.url;
        this.items.forEach(item => {
            if (path && path.startsWith(item.path)) {
                this.nav.emit(item);
            }
        })
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
