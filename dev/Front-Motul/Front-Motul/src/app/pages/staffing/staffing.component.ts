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
  
  collabSubmitted = false;
  imputationSubmitted = false;
  projectSubmitted = false;
  
  collabForm: Collaborator = { collaborateur: '', dateDemarrage: '', profilProfessionnel: '', anciennete: '', salaire: 0 };
  imputationForm: Imputation = { collaborateur: '', collaborateurId: undefined, projet: '', projetId: undefined, mois: '', annee: '2024', nbrJours: 0 };
  projectForm: Project = { name: '', description: '', clientName: '', startDate: '', endDate: '', turnover: 0 };
  
  searchTerm = '';

  // Sorting state
  collabSortColumn = '';
  collabSortDirection: 'asc' | 'desc' = 'asc';
  projectSortColumn = '';
  projectSortDirection: 'asc' | 'desc' = 'asc';

  get filteredCollaborators(): Collaborator[] {
    let list = [...this.collaborators];
    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase().trim();
      list = list.filter(c => 
        (c.collaborateur || '').toLowerCase().includes(term) ||
        (c.profilProfessionnel || '').toLowerCase().includes(term) ||
        (c.anciennete || '').toLowerCase().includes(term) ||
        (c.dateDemarrage || '').toLowerCase().includes(term) ||
        String(c.salaire || '').includes(term)
      );
    }
    
    if (this.collabSortColumn) {
      const col = this.collabSortColumn;
      const dir = this.collabSortDirection === 'asc' ? 1 : -1;
      list.sort((a: any, b: any) => {
        const valA = a[col];
        const valB = b[col];
        
        if (col === 'salaire') {
          return (Number(valA || 0) - Number(valB || 0)) * dir;
        }
        if (col === 'dateDemarrage') {
          const dateA = new Date(valA || '').getTime();
          const dateB = new Date(valB || '').getTime();
          return (dateA - dateB) * dir;
        }
        if (col === 'anciennete') {
          const numA = parseInt(valA, 10) || 0;
          const numB = parseInt(valB, 10) || 0;
          return (numA - numB) * dir;
        }
        return String(valA || '').localeCompare(String(valB || '')) * dir;
      });
    }
    return list;
  }

  get filteredProjects(): Project[] {
    let list = [...this.projects];
    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase().trim();
      list = list.filter(p => 
        (p.name || '').toLowerCase().includes(term) ||
        (p.description || '').toLowerCase().includes(term) ||
        (p.clientName || '').toLowerCase().includes(term) ||
        (p.startDate || '').toLowerCase().includes(term) ||
        (p.endDate || '').toLowerCase().includes(term) ||
        String(p.turnover || '').includes(term)
      );
    }
    
    if (this.projectSortColumn) {
      const col = this.projectSortColumn;
      const dir = this.projectSortDirection === 'asc' ? 1 : -1;
      list.sort((a: any, b: any) => {
        const valA = a[col];
        const valB = b[col];
        
        if (col === 'turnover') {
          return (Number(valA || 0) - Number(valB || 0)) * dir;
        }
        if (col === 'startDate' || col === 'endDate') {
          const dateA = new Date(valA || '').getTime();
          const dateB = new Date(valB || '').getTime();
          return (dateA - dateB) * dir;
        }
        return String(valA || '').localeCompare(String(valB || '')) * dir;
      });
    }
    return list;
  }

  get filteredImputations(): Imputation[] {
    if (!this.searchTerm.trim()) return this.imputations;
    const term = this.searchTerm.toLowerCase().trim();
    return this.imputations.filter(i => 
      (i.collaborateur || '').toLowerCase().includes(term) ||
      (i.projet || '').toLowerCase().includes(term) ||
      (i.mois || '').toLowerCase().includes(term) ||
      (i.annee || '').toLowerCase().includes(term) ||
      String(i.nbrJours || '').includes(term)
    );
  }

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
    this.searchTerm = '';
    this.loadData();
  }
  
  // Collaborators CRUD
  openCollaboratorModal(): void {
    this.showCollaboratorModal = true;
    this.collabSubmitted = false;
    this.collabForm = { id: undefined, collaborateur: '', dateDemarrage: '', profilProfessionnel: '', anciennete: '', salaire: 0 };
  }
  
  closeCollaboratorModal(): void {
    this.showCollaboratorModal = false;
  }
  
  saveCollaborator(): void {
    this.collabSubmitted = true;
    if (!this.collabForm.collaborateur || !this.collabForm.dateDemarrage || !this.collabForm.profilProfessionnel || !this.collabForm.anciennete || !this.collabForm.salaire) return;
    if (this.isCollabDateInvalid()) return;
    this.staffingService.createCollaborator(this.collabForm).subscribe({
      next: () => {
        this.closeCollaboratorModal();
        this.loadData();
      }
    });
  }

  isCollabDateInvalid(): boolean {
    if (!this.collabForm.dateDemarrage) return false;
    const regex = /^\d{4}-\d{2}-\d{2}$/;
    if (!regex.test(this.collabForm.dateDemarrage.trim())) return true;
    const d = new Date(this.collabForm.dateDemarrage);
    return isNaN(d.getTime());
  }

  editCollaborator(collab: Collaborator): void {
    this.collabForm = { ...collab };
    this.collabSubmitted = false;
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
    this.imputationSubmitted = false;
    this.imputationForm = { id: undefined, collaborateur: '', collaborateurId: undefined, projet: '', projetId: undefined, mois: '', annee: '2024', nbrJours: 0 };
    this.loadAllForImputation();
  }
  
  closeImputationModal(): void {
    this.showImputationModal = false;
  }
  
  saveImputation(): void {
    this.imputationSubmitted = true;
    if (!this.imputationForm.collaborateurId || !this.imputationForm.projetId || !this.imputationForm.mois || !this.imputationForm.annee || this.imputationForm.nbrJours === undefined || this.imputationForm.nbrJours === null) return;
    if (this.isImputationMoisInvalid() || this.isImputationAnneeInvalid() || this.isImputationNbrJoursInvalid()) return;
    this.staffingService.createImputation(this.imputationForm).subscribe({
      next: () => {
        this.closeImputationModal();
        this.loadData();
      }
    });
  }

  isImputationMoisInvalid(): boolean {
    if (!this.imputationForm.mois) return false;
    const m = parseInt(this.imputationForm.mois, 10);
    return isNaN(m) || m < 1 || m > 12;
  }

  isImputationAnneeInvalid(): boolean {
    if (!this.imputationForm.annee) return false;
    const y = parseInt(this.imputationForm.annee, 10);
    return isNaN(y) || y < 2000 || y > 2100 || !/^\d{4}$/.test(this.imputationForm.annee.trim());
  }

  isImputationNbrJoursInvalid(): boolean {
    const days = this.imputationForm.nbrJours;
    if (days === undefined || days === null) return false;
    return days < 0 || days > 31;
  }

  editImputation(imp: Imputation): void {
    this.imputationForm = { ...imp };
    this.imputationSubmitted = false;
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
    this.projectSubmitted = false;
    this.projectForm = { id: undefined, name: '', description: '', clientName: '', startDate: '', endDate: '', turnover: 0 };
  }

  closeProjectModal(): void {
    this.showProjectModal = false;
  }

  saveProject(): void {
    this.projectSubmitted = true;
    if (!this.projectForm.name || !this.projectForm.clientName || !this.projectForm.startDate || !this.projectForm.endDate || !this.projectForm.turnover) return;
    if (this.isProjectStartDateInvalid() || this.isProjectEndDateInvalid() || this.isProjectDateRangeInvalid()) return;
    this.staffingService.createProject(this.projectForm).subscribe({
      next: () => {
        this.closeProjectModal();
        this.loadData();
      }
    });
  }

  isProjectStartDateInvalid(): boolean {
    if (!this.projectForm.startDate) return false;
    const regex = /^\d{4}-\d{2}-\d{2}$/;
    if (!regex.test(this.projectForm.startDate.trim())) return true;
    const d = new Date(this.projectForm.startDate);
    return isNaN(d.getTime());
  }

  isProjectEndDateInvalid(): boolean {
    if (!this.projectForm.endDate) return false;
    const regex = /^\d{4}-\d{2}-\d{2}$/;
    if (!regex.test(this.projectForm.endDate.trim())) return true;
    const d = new Date(this.projectForm.endDate);
    return isNaN(d.getTime());
  }

  isProjectDateRangeInvalid(): boolean {
    if (!this.projectForm.startDate || !this.projectForm.endDate) return false;
    if (this.isProjectStartDateInvalid() || this.isProjectEndDateInvalid()) return false;
    const start = new Date(this.projectForm.startDate);
    const end = new Date(this.projectForm.endDate);
    return end < start;
  }

  toggleCollabSort(col: string): void {
    if (this.collabSortColumn === col) {
      this.collabSortDirection = this.collabSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.collabSortColumn = col;
      this.collabSortDirection = 'asc';
    }
  }

  toggleProjectSort(col: string): void {
    if (this.projectSortColumn === col) {
      this.projectSortDirection = this.projectSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.projectSortColumn = col;
      this.projectSortDirection = 'asc';
    }
  }

  editProject(proj: Project): void {
    this.projectForm = { ...proj };
    this.projectSubmitted = false;
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
