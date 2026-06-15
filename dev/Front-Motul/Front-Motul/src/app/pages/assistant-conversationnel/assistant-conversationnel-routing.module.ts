import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {ChatSidebarComponent} from "./chat-sidebar/chat-sidebar.component";

const routes: Routes = [
  {
    path: '',
    redirectTo: 'chat',
    pathMatch: 'full'
  },
  {
    path: 'chat',
    component: ChatSidebarComponent
  },
];
@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AssistantConversationnelRoutingModule { }
