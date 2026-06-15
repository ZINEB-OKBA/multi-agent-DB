import { Routes } from '@angular/router';
import { AdminComponent } from './layout/admin/admin.component';
import {AuthGuard} from './core/auth/auth.guard';

export const routes: Routes = [
    {
        path: '',
        canActivate: [AuthGuard],
        component: AdminComponent,
        loadChildren: () => import('./pages/pages.module').then((m) => m.PagesModule )
    },
    {
        path: 'auth',
        loadChildren: () => import('./auth/auth.module').then((e) => e.AuthModule)
    },
    {
        path: '**',
        redirectTo: '/404',
    },
];
