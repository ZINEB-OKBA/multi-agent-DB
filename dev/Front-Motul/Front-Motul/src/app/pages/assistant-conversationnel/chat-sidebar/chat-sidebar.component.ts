import { Component, OnInit, HostListener } from '@angular/core';
import { ConversationService } from '../../../core/services/assistant-conversationnel/conversation.service';
import { AlertService } from '../../../core/auth/alert.service';
import { ProjectService } from '../../../core/services/data-base/project-service/project.service';
import { Project } from '../../../core/models/project.model';

@Component({
  selector: 'app-chat-sidebar',
  standalone: false,
  templateUrl: './chat-sidebar.component.html',
  styleUrl: './chat-sidebar.component.scss'
})
export class ChatSidebarComponent implements OnInit {

  // ── Responsive ──────────────────────────────────────────────────────────
  isSidebarOpen = true;
  isDesktop     = true;

  // ── Conversations ────────────────────────────────────────────────────────
  conversationList: Array<any> = [];
  term!: string;
  selectedConversation: any = null;

  // ── Projets ──────────────────────────────────────────────────────────────
  projects: Project[]       = [];
  projectsLoading           = false;
  selectedProjectName       = '';   // nom envoyé à Python : { "project": selectedProjectName }

  constructor(
      private conversationService: ConversationService,
      private alertService: AlertService,
      private projectService: ProjectService      // ← service déjà créé dans la session précédente
  ) {}

  ngOnInit(): void {
    this.checkScreenSize();
    this.onLoadConversation();
    this.loadProjects();
  }

  // ── Chargement des projets depuis Spring Boot ────────────────────────────

  loadProjects(): void {
    this.projectsLoading = true;
    this.projectService.getAllProjects().subscribe({
      next: (list) => {
        this.projects        = list;
        this.projectsLoading = false;

        // Pré-sélectionne le dernier projet utilisé (stocké en mémoire par le service)
        const remembered = this.projectService.getSelectedProject();
        if (remembered) {
          this.selectedProjectName = remembered.name;
        } else if (list.length === 1) {
          // Auto-sélection si un seul projet existe
          this.selectedProjectName = list[0].name;
          this.projectService.selectProject(list[0]);
        }
      },
      error: () => {
        this.projectsLoading = false;
      }
    });
  }

  // Appelé quand l'utilisateur change de projet dans le dropdown
  onProjectChange(projectName: string): void {
    const found = this.projects.find(p => p.name === projectName);
    if (found) {
      // Met à jour l'état partagé (utilisé par les autres composants navigation)
      this.projectService.selectProject(found);
    }
  }

  // ── Conversations ────────────────────────────────────────────────────────

  onLoadConversation(): void {
    const filter = { page: { page: 0 }, term: this.term };
    this.conversationService.find(filter).subscribe(response => {
      this.conversationList = response?.content;
    });
  }

  onSelectConversation(conversation: any): void {
    this.selectedConversation = conversation;
    if (!this.isDesktop) this.isSidebarOpen = false;
  }

  addNewConversation(): void {
    this.selectedConversation = { id: null, messages: [] };
    if (!this.isDesktop) this.isSidebarOpen = false;
  }

  deleteConversation(id: any): void {
    this.alertService.confirmDelete().then(result => {
      if (result.isConfirmed) {
        this.conversationService.delete(id).subscribe(() => {
          this.onLoadConversation();
          this.alertService.successAlert();
        });
      }
    });
  }

  onConversationCreated(conversation: any): void {
    this.onLoadConversation();
    this.selectedConversation = conversation;
  }

  rename(conversation: any): void {
    if (!conversation.editing) {
      conversation.editing = true;
      return;
    }
    conversation.editing = false;
    this.conversationService.rename(conversation).subscribe(() => {
      this.onLoadConversation();
      this.alertService.successAlert();
    });
  }

  // ── Responsive ──────────────────────────────────────────────────────────

  @HostListener('window:resize')
  onResize(): void { this.checkScreenSize(); }

  checkScreenSize(): void {
    this.isDesktop     = window.innerWidth >= 1024;
    this.isSidebarOpen = this.isDesktop;
  }

  toggleSidebar(): void {
    this.isSidebarOpen = !this.isSidebarOpen;
  }
}