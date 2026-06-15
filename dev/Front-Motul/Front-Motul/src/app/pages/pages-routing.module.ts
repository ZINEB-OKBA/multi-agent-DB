import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {HomeComponent} from './home/home.component';
import {PageNotFoundComponent} from "./page-not-found/page-not-found.component";

const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full'
  },
  {
    path: 'home',
    component: HomeComponent,
  },
  {
    path: 'administration',
    loadChildren: () => import('./administration/administration.module').then(m => m.AdministrationModule),
  },
  {
    path: 'parametrage',
    loadChildren: () => import('./parametrage/parametrage.module').then(m => m.ParametrageModule),
  },
  {
    path: 'assistant-conversationnel',
    loadChildren: () => import('./assistant-conversationnel/assistant-conversationnel.module').then(m => m.AssistantConversationnelModule),
  },
  {
    path: 'data-base',
    loadChildren: () => import('./data-base/data-base.module').then(m => m.DataBaseModule),
  },
  {
    path: '404',
    component: PageNotFoundComponent },
];


@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PagesRoutingModule { }
