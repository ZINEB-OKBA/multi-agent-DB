import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ProjectService } from '../../../core/services/data-base/project-service/project.service';
import { DocumentDownloadService } from '../../../core/services/document-download.service';

// ✅ Chemin mis à jour et aligné sur l'architecture de votre dossier core/models
import {
  Project, DocumentResponse, DocumentType,
  PDF_EXTENSIONS, EXCEL_EXTENSIONS
} from '../../../core/models/project.model';

@Component({
  selector: 'app-documents-list',
  standalone: false,
  templateUrl: './documents-list.component.html',
  styleUrls: ['./document-list.component.scss'] // ✅ Corrigé au singulier pour correspondre exactement à votre fichier physique
})
export class DocumentsListComponent implements OnInit {

  project: Project | null = null;
  projectId!: number;
  documentType!: DocumentType;

  allDocuments: DocumentResponse[] = [];
  filteredDocuments: DocumentResponse[] = [];
  isLoading = false;

  // ID du doc en cours de téléchargement (pour afficher le spinner dans le bouton d'action)
  downloadingId: number | null = null;

  showUploadModal = false;
  isUploading     = false;
  uploadProgress  = 0;
  uploadForm = { file: null as File | null, indexIA: true };

  constructor(
      private route:           ActivatedRoute,
      private router:          Router,
      private projectService:  ProjectService,
      private downloadService: DocumentDownloadService
  ) {}

  ngOnInit(): void {
    this.projectId    = Number(this.route.snapshot.paramMap.get('id'));
    this.documentType = (this.route.snapshot.queryParamMap.get('type') as DocumentType) || 'pdf';

    this.project = this.projectService.getSelectedProject();

    if (!this.project || this.project.id !== this.projectId) {
      this.projectService.getAllProjects().subscribe({
        next: (projects) => {
          this.project = projects.find(p => p.id === this.projectId) || null;
          if (this.project) {
            this.projectService.selectProject(this.project);
            this.loadDocuments();
          } else {
            this.router.navigate(['/projects']);
          }
        },
        error: () => this.router.navigate(['/projects'])
      });
    } else {
      this.loadDocuments();
    }
  }

  // ── Getters ──────────────────────────────────────────────────────────────

  get isPdf(): boolean { return this.documentType === 'pdf'; }

  get acceptedExtensions(): string {
    return this.isPdf ? PDF_EXTENSIONS.join(',') : EXCEL_EXTENSIONS.join(',');
  }

  get indexedCount(): number {
    return this.filteredDocuments.filter(d => d.isIndexed).length;
  }

  // ── Documents ─────────────────────────────────────────────────────────────

  loadDocuments(): void {
    this.isLoading = true;
    this.projectService.getProjectDocuments(this.projectId).subscribe({
      next: (docs) => {
        this.allDocuments = docs;
        this.applyFilter();
        this.isLoading = false;
      },
      error: () => { this.isLoading = false; }
    });
  }

  private applyFilter(): void {
    const extensions = this.isPdf ? PDF_EXTENSIONS : EXCEL_EXTENSIONS;
    this.filteredDocuments = this.allDocuments.filter(doc => {
      const ext = '.' + doc.fileName.split('.').pop()?.toLowerCase();
      return extensions.includes(ext);
    });
  }

  // ── TÉLÉCHARGEMENT ────────────────────────────────────────────────────────
  downloadDocument(doc: DocumentResponse): void {
    if (this.downloadingId === doc.id) return;
    this.downloadingId = doc.id;

    // ✅ Envoi de la requête relative avec transmission du nom original en secours (CORS)
    this.downloadService.downloadById(doc.id, doc.fileName);

    // Réinitialisation de l'icône après 3 secondes
    setTimeout(() => { this.downloadingId = null; }, 3000);
  }

  // ── Indexation ────────────────────────────────────────────────────────────

  triggerIndex(documentId: number): void {
    this.projectService.triggerIndexing(documentId).subscribe({
      next: () => this.loadDocuments(),
      error: (err) => console.error('Erreur indexation', err)
    });
  }

  deleteDocument(documentId: number): void {
    if (!confirm('Supprimer ce fichier ?')) return;
    this.projectService.deleteDocument(documentId).subscribe({
      next: () => this.loadDocuments(),
      error: (err) => console.error('Erreur suppression', err)
    });
  }

  // ── Upload ────────────────────────────────────────────────────────────────

  openUploadModal(): void { this.showUploadModal = true; }

  closeUploadModal(): void {
    if (this.isUploading) return;
    this.showUploadModal = false;
    this.uploadProgress  = 0;
    this.uploadForm      = { file: null, indexIA: true };
  }

  onFileSelected(event: any): void {
    const file: File = event.target.files[0];
    if (file) this.uploadForm.file = file;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    const file = event.dataTransfer?.files[0];
    if (file) this.uploadForm.file = file;
  }

  submitUpload(): void {
    if (!this.uploadForm.file || this.isUploading) return;
    this.isUploading   = true;
    this.uploadProgress = 10;

    const reader = new FileReader();
    reader.onprogress = (e) => {
      if (e.lengthComputable) this.uploadProgress = Math.round((e.loaded / e.total) * 70);
    };
    reader.onload = () => {
      this.uploadProgress = 75;
      this.projectService.uploadDocument({
        projectId: this.projectId,
        fileName:  this.uploadForm.file!.name,
        content:   reader.result as string
      }).subscribe({
        next: () => {
          this.uploadProgress = 100;
          this.isUploading    = false;
          setTimeout(() => { this.closeUploadModal(); this.loadDocuments(); }, 400);
        },
        error: (err) => {
          this.isUploading = false;
          this.uploadProgress = 0;
          alert(err?.error || "Erreur lors de l'envoi.");
        }
      });
    };
    reader.onerror = () => { this.isUploading = false; alert('Impossible de lire le fichier.'); };
    reader.readAsDataURL(this.uploadForm.file);
  }

  // ── Utilitaires ───────────────────────────────────────────────────────────

  getExtension(fileName: string): string {
    return fileName?.split('.').pop()?.toUpperCase() || '';
  }

  getFileIcon(fileName: string): string {
    const ext = fileName?.split('.').pop()?.toLowerCase();
    const icons: Record<string, string> = {
      pdf: 'ki-file-pdf', doc: 'ki-file-doc', docx: 'ki-file-doc',
      xlsx: 'ki-file-sheet', xls: 'ki-file-sheet', xlsm: 'ki-file-sheet', csv: 'ki-file-binary'
    };
    return icons[ext || ''] || 'ki-file';
  }

  formatSize(bytes: number): string {
    if (bytes < 1024)        return `${bytes} o`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
    return `${(bytes / 1024 / 1024).toFixed(1)} Mo`;
  }

  goBack(): void { this.router.navigate(['/data-base/projects', this.projectId]); }
}