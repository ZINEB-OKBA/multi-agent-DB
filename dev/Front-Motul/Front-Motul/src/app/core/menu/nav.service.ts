import {Injectable} from '@angular/core';
import {BehaviorSubject} from 'rxjs';
import {Router} from '@angular/router';
import {RoleEnum} from "../enums/role.enum";
import {TranslateService} from "@ngx-translate/core";

// Menu
export interface Menu {
    path?: string;
    title?: string;
    icon?: string;
    type: 'link' | 'sub';
    children?: Menu[];
    authorities: Array<RoleEnum>;
    hidden?: boolean;

}

@Injectable({
    providedIn: 'root',
})
export class NavService {
    items = new BehaviorSubject<Menu[]>([]);

    constructor(private router: Router, private translate: TranslateService) {
        const MENUITEMS = (): Menu[] => [
            {
                path: '/assistant-conversationnel',
                icon: `ki-filled ki-android`,
                title: 'MODULES.CHAT.CONVERSATIONAL_ASSISTANT',
                type: 'sub',
                children: [
                    {
                        path: '/assistant-conversationnel/chat',
                        icon: `ki-filled ki-messages`,
                        title: 'MODULES.CHAT.CONVERSATIONAL_ASSISTANT',
                        type: 'link',
                        authorities: [RoleEnum.ROLE_ASSISTANT_CONVERSATIONNEL]
                    }
                ],
                authorities: [RoleEnum.ROLE_ASSISTANT_CONVERSATIONNEL]
            },
            {
                path: '/administration/',
                icon: `ki-filled ki-brifecase-cros`,
                title: 'MODULES.MENU.ADMIN',
                type: 'sub',
                children: [
                    {
                        path: '/administration/utilisateurs',
                        icon: `ki-filled ki-profile-circle`,
                        title: 'MODULES.MENU.USERS_MANAGEMENT',
                        type: 'link',
                        authorities: [RoleEnum.ROLE_GESTION_UTILISATEUR]
                    },
                    {
                        path: '/administration/habilitation',
                        icon: `ki-filled ki-security-user`,
                        title: 'MODULES.MENU.ROLES_MANAGEMENT',
                        type: 'link',
                        authorities: [RoleEnum.ROLE_GESTION_UTILISATEUR]
                    }
                ],
                authorities: [RoleEnum.ROLE_GESTION_UTILISATEUR]
            },
            {
                path: '/data-base/',
                icon: `ki-filled ki-financial-schedule`,
                title: 'MODULES.MENU.DATA_BASE',
                type: 'sub',
                children: [
                    {
                        path: '/data-base/',
                        icon: `ki-filled ki-data`,
                        title: 'MODULES.MENU.DATA_BASE',
                        type: 'link',
                        authorities: [RoleEnum.ROLE_AFFICHER_DATABASE]
                    }
                ],
                authorities: [RoleEnum.ROLE_AFFICHER_DATABASE]
            },
            {
                path: '/staffing/',
                icon: `ki-filled ki-people`,
                title: 'MODULES.MENU.STAFFING',
                type: 'sub',
                children: [
                    {
                        path: '/staffing/',
                        icon: `ki-filled ki-people`,
                        title: 'MODULES.MENU.STAFFING',
                        type: 'link',
                        authorities: [RoleEnum.ROLE_AFFICHER_DATABASE]
                    }
                ],
                authorities: [RoleEnum.ROLE_AFFICHER_DATABASE]
            },
            {
                path: '/administration/utilisateurs/profile',
                icon: `ki-filled ki-profile-circle`,
                title: 'MODULES.PROFILES.TITLE',
                type: 'sub',
                children: [
                    {
                        path: '/administration/utilisateurs/profile',
                        icon: `ki-filled ki-profile-circle`,
                        title: 'MODULES.PROFILES.TITLE',
                        type: 'link',
                        authorities: []
                    }
                ],
                authorities: []
            }
        ];


        this.items.next(MENUITEMS());

        this.translate.onLangChange.subscribe(() => {
            this.items.next(MENUITEMS());
        });
    }
}
