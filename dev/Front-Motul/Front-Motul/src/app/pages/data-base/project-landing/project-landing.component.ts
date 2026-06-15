import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ProjectService } from '../../../core/services/data-base/project-service/project.service';
import { Project } from '../../../core/models/project.model';

@Component({
  selector: 'app-project-landing',
  standalone: false,
  templateUrl: './project-landing.component.html'
})
export class ProjectLandingComponent implements OnInit {

  project: Project | null = null;
  projectId!: number;

  constructor(
      private route: ActivatedRoute,
      private router: Router,
      private projectService: ProjectService
  ) {}

  ngOnInit(): void {
    // Récupère l'id depuis l'URL (/projects/42)
    this.projectId = Number(this.route.snapshot.paramMap.get('id'));

    // Récupère le projet depuis le service (état en mémoire, chargé par ProjectsListComponent)
    // Si l'utilisateur arrive directement sur cette URL (ex: refresh), on recharge depuis l'API
    this.project = this.projectService.getSelectedProject();

    if (!this.project || this.project.id !== this.projectId) {
      // Cas du refresh page ou navigation directe : on recharge les projets
      this.projectService.getAllProjects().subscribe({
        next: (projects) => {
          this.project = projects.find(p => p.id === this.projectId) || null;
          if (this.project) {
            this.projectService.selectProject(this.project);
          } else {
            // Projet introuvable → retour à la liste
            this.router.navigate(['/projects']);
          }
        },
        error: () => this.router.navigate(['/projects'])
      });
    }
  }

  // Navigue vers la liste de documents filtrée par type
  navigateTo(type: 'pdf' | 'excel'): void {
    this.router.navigate(['documents'], {
      relativeTo: this.route,
      queryParams: { type }
    });
  }

  goBack(): void {
    this.router.navigate(['../'], { relativeTo: this.route });  }
}