import { Component, OnInit } from '@angular/core';
import { StaffingService, Collaborator, Imputation, Project } from '../../core/services/staffing/staffing.service';

@Component({
  selector: 'app-staffing',
  standalone: false,
  templateUrl: './staffing.component.html',
  styleUrl: './staffing.component.scss'
})
export class StaffingComponent implements OnInit {
  activeTab: 'collaborateurs' | 'projets' | 'imputations' = 'collaborateurs';
  
  collaborators: Collaborator[] = [];
  imputations: Imputation[] = [];
  projects: Project[] = [];
  
  isLoading = false;
  
  // Modals
  showCollaboratorModal = false;
  showImputationModal = false;
  showProjectModal = false;
  
  collabForm: Collaborator = { collaborateur: '', dateDemarrage: '', profilProfessionnel: '', anciennete: '', salaire: 0 };
  imputationForm: Imputation = { collaborateur: '', collaborateurId: undefined, projet: '', projetId: undefined, mois: '', annee: '2024', nbrJours: 0 };
  projectForm: Project = { name: '', description: '', clientName: '', startDate: '', endDate: '', turnover: 0 };
  
  constructor(private staffingService: StaffingService) {}
  
  ngOnInit(): void {
    this.loadData();
  }
  
  loadData(): void {
    this.isLoading = true;
    if (this.activeTab === 'collaborateurs') {
      this.staffingService.getCollaborators().subscribe({
        next: (res) => {
          this.collaborators = res;
          this.isLoading = false;
        },
        error: () => this.isLoading = false
      });
    } else if (this.activeTab === 'imputations') {
      this.staffingService.getImputations().subscribe({
        next: (res) => {
          this.imputations = res;
          this.isLoading = false;
        },
        error: () => this.isLoading = false
      });
    } else if (this.activeTab === 'projets') {
      this.staffingService.getProjects().subscribe({
        next: (res) => {
          this.projects = res;
          this.isLoading = false;
        },
        error: () => this.isLoading = false
      });
    }
  }
  
  switchTab(tab: 'collaborateurs' | 'projets' | 'imputations'): void {
    this.activeTab = tab;
    this.loadData();
  }
  
  // Collaborators CRUD
  openCollaboratorModal(): void {
    this.showCollaboratorModal = true;
    this.collabForm = { id: undefined, collaborateur: '', dateDemarrage: '', profilProfessionnel: '', anciennete: '', salaire: 0 };
  }
  
  closeCollaboratorModal(): void {
    this.showCollaboratorModal = false;
  }
  
  saveCollaborator(): void {
    if (!this.collabForm.collaborateur || !this.collabForm.salaire) return;
    this.staffingService.createCollaborator(this.collabForm).subscribe({
      next: () => {
        this.closeCollaboratorModal();
        this.loadData();
      }
    });
  }

  editCollaborator(collab: Collaborator): void {
    this.collabForm = { ...collab };
    this.showCollaboratorModal = true;
  }
  
  deleteCollaborator(id: number): void {
    if (confirm('Supprimer ce collaborateur ?')) {
      this.staffingService.deleteCollaborator(id).subscribe({
        next: () => this.loadData()
      });
    }
  }
  
  loadAllForImputation(): void {
    this.staffingService.getCollaborators().subscribe({
      next: (res) => this.collaborators = res
    });
    this.staffingService.getProjects().subscribe({
      next: (res) => this.projects = res
    });
  }

  onCollaboratorChange(event: any): void {
    const selectedId = Number(this.imputationForm.collaborateurId);
    const selectedCollab = this.collaborators.find(c => c.id === selectedId);
    if (selectedCollab) {
      this.imputationForm.collaborateur = selectedCollab.collaborateur;
    }
  }

  onProjectChange(event: any): void {
    const selectedId = Number(this.imputationForm.projetId);
    const selectedProj = this.projects.find(p => p.id === selectedId);
    if (selectedProj) {
      this.imputationForm.projet = selectedProj.name;
    }
  }

  // Imputations CRUD
  openImputationModal(): void {
    this.showImputationModal = true;
    this.imputationForm = { id: undefined, collaborateur: '', collaborateurId: undefined, projet: '', projetId: undefined, mois: '', annee: '2024', nbrJours: 0 };
    this.loadAllForImputation();
  }
  
  closeImputationModal(): void {
    this.showImputationModal = false;
  }
  
  saveImputation(): void {
    if (!this.imputationForm.collaborateurId || !this.imputationForm.projetId || !this.imputationForm.mois || !this.imputationForm.nbrJours) return;
    this.staffingService.createImputation(this.imputationForm).subscribe({
      next: () => {
        this.closeImputationModal();
        this.loadData();
      }
    });
  }

  editImputation(imp: Imputation): void {
    this.imputationForm = { ...imp };
    this.loadAllForImputation();
    this.showImputationModal = true;
  }
  
  deleteImputation(id: number): void {
    if (confirm('Supprimer cette imputation ?')) {
      this.staffingService.deleteImputation(id).subscribe({
        next: () => this.loadData()
      });
    }
  }

  // Projects CRUD
  openProjectModal(): void {
    this.showProjectModal = true;
    this.projectForm = { id: undefined, name: '', description: '', clientName: '', startDate: '', endDate: '', turnover: 0 };
  }

  closeProjectModal(): void {
    this.showProjectModal = false;
  }

  saveProject(): void {
    if (!this.projectForm.name || !this.projectForm.clientName) return;
    this.staffingService.createProject(this.projectForm).subscribe({
      next: () => {
        this.closeProjectModal();
        this.loadData();
      }
    });
  }

  editProject(proj: Project): void {
    this.projectForm = { ...proj };
    this.showProjectModal = true;
  }

  deleteProject(id: number): void {
    if (confirm('Supprimer ce projet ?')) {
      this.staffingService.deleteProject(id).subscribe({
        next: () => this.loadData()
      });
    }
  }

  // Get Initials for Circle Avatar
  getInitials(collaborateur: string): string {
    if (!collaborateur) return '';
    const parts = collaborateur.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return parts[0][0].toUpperCase();
  }
}
