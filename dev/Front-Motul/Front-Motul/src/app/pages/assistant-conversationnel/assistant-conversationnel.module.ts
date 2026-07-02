import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { AssistantConversationnelRoutingModule } from './assistant-conversationnel-routing.module';
import { ChatMessagesComponent } from './chat-messages/chat-messages.component';
import { ChatSidebarComponent } from './chat-sidebar/chat-sidebar.component';
import {FormsModule, ReactiveFormsModule} from "@angular/forms";
import {TranslatePipe} from "@ngx-translate/core";


@NgModule({
  declarations: [
    ChatMessagesComponent,
    ChatSidebarComponent
  ],
    imports: [
        CommonModule,
        AssistantConversationnelRoutingModule,
        FormsModule,
        ReactiveFormsModule,
        TranslatePipe
    ]
})
export class AssistantConversationnelModule { }
