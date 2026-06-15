import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ProjectService } from '../../../core/services/data-base/project-service/project.service';
import { Project } from '../../../core/models/project.model';
import { ActivatedRoute } from '@angular/router';
@Component({
  selector: 'app-projects-list',
  standalone: false,
  templateUrl: './project-list.component.html'
})
export class ProjectsListComponent implements OnInit {

  projects: Project[] = [];
  isLoading = false;

  // Modale création
  showCreateModal = false;
  isCreating = false;
  createForm = { name: '', description: '' };

  constructor(
      private projectService: ProjectService,
      private router: Router,
      private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    this.loadProjects();
  }

  loadProjects(): void {
    this.isLoading = true;
    this.projectService.getAllProjects().subscribe({
      next: (projects) => {
        this.projects = projects;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Erreur chargement projets', err);
        this.isLoading = false;
      }
    });
  }

  // ── Sélection d'un projet → stocke en mémoire → navigue ─────────────────

  selectProject(project: Project): void {
    // Stocke le projet sélectionné dans le service (état en mémoire, pas de BDD)
    this.projectService.selectProject(project);
    // Navigue vers la page du projet
    this.router.navigate(['projects', project.id], { relativeTo: this.route });  }

  // ── Suppression ─────────────────────────────────────────────────────────

  deleteProject(event: Event, id: number): void {
    event.stopPropagation(); // Empêche la sélection du projet
    if (!confirm('Supprimer ce projet et tous ses documents ?')) return;

    this.projectService.deleteProject(id).subscribe({
      next: () => this.loadProjects(),
      error: (err) => console.error('Erreur suppression', err)
    });
  }

  // ── Création ─────────────────────────────────────────────────────────────

  openCreateModal(): void {
    this.showCreateModal = true;
  }

  closeCreateModal(): void {
    if (this.isCreating) return;
    this.showCreateModal = false;
    this.createForm = { name: '', description: '' };
  }

  submitCreate(): void {
    if (!this.createForm.name.trim() || this.isCreating) return;
    this.isCreating = true;

    this.projectService.createProject({
      name: this.createForm.name.trim(),
      description: this.createForm.description.trim() || undefined
    }).subscribe({
      next: () => {
        this.isCreating = false;
        this.closeCreateModal();
        this.loadProjects();
      },
      error: (err) => {
        this.isCreating = false;
        console.error('Erreur création projet', err);
      }
    });
  }
}