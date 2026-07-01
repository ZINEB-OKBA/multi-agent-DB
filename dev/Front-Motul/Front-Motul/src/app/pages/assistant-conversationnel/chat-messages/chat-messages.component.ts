import {
  AfterViewChecked,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  Output,
  SimpleChanges,
  ViewChild
} from '@angular/core';
import { GraphPayload } from '../../../core/models/GraphPayload';
import Chart from 'chart.js/auto';
import type { ChartConfiguration } from 'chart.js';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ConversationService } from '../../../core/services/assistant-conversationnel/conversation.service';
import { AlertService } from '../../../core/auth/alert.service';
import { ProjectService } from '../../../core/services/data-base/project-service/project.service';

// ── 1. AJOUT DES IMPORTS POUR LE TÉLÉCHARGEMENT DES SOURCES ──────────────────
import { DocumentDownloadService } from '../../../core/services/document-download.service';

@Component({
  selector: 'app-chat-messages',
  standalone: false,
  templateUrl: './chat-messages.component.html',
  styleUrl: './chat-messages.component.scss'
})
export class ChatMessagesComponent implements OnInit, OnChanges, AfterViewChecked, OnDestroy {

  @ViewChild('chatContainer', { static: false }) chatContainer!: ElementRef;

  // ── Inputs ───────────────────────────────────────────────────────────────

  /** Conversation courante (passée par chat-sidebar) */
  @Input() conversation: any;

  /**
   * Nom du projet sélectionné dans le dropdown (passé par chat-sidebar).
   * Envoyé tel quel à Python : POST /api/chat → { "project": selectedProject }
   */
  @Input() selectedProject: string = '';

  @Output() conversationCreated = new EventEmitter<any>();

  // ── État ─────────────────────────────────────────────────────────────────

  isLoading            = false;
  messages: any[]      = [];
  isScrolledToBottom   = true;
  protected form!: FormGroup;
  private charts: Record<string, Chart> = {};
  private pendingScroll = false;
  
  isStaffingAgentMode  = false;
  
  setStaffingMode(mode: boolean): void {
    this.isStaffingAgentMode = mode;
  }

  // ── 2. PROPRIÉTÉ POUR LE SPINNER DE TÉLÉCHARGEMENT DES SOURCES ─────────────
  downloadingSource: string | null = null;

  // ── 3. INJECTION DU SERVICE DANS LE CONSTRUCTEUR ───────────────────────────
  constructor(
      private conversationService: ConversationService,
      private fb: FormBuilder,
      private alertService: AlertService,
      private cd: ChangeDetectorRef,
      private downloadService: DocumentDownloadService,
      private projectService: ProjectService
  ) {}

  // ── Lifecycle ─────────────────────────────────────────────────────────────

  ngOnInit(): void {
    this.initForm();
  }

  ngAfterViewChecked(): void {
    if (this.pendingScroll) {
      this.scrollToBottom();
      this.pendingScroll = false;
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['conversation'] && this.conversation) {
      if (!this.conversation.id) {
        this.messages = [];
        this.form.patchValue({ conversation: null });
        return;
      }
      this.form.patchValue({ conversation: this.conversation });
      this.loadMessages(this.conversation.id);
    }
  }

  ngOnDestroy(): void {
    Object.values(this.charts).forEach(c => { try { c.destroy(); } catch {} });
    this.charts = {};
  }

  @HostListener('window:resize')
  onResize(): void {
    setTimeout(() => this.scrollToBottom(), 150);
  }

  // ── Formulaire ────────────────────────────────────────────────────────────

  protected initForm(): void {
    this.form = this.fb.group({
      content:      [null, Validators.required],
      conversation: [null]
    });
  }

  // ── Chargement des messages ───────────────────────────────────────────────

  loadMessages(conversationId: number): void {
    this.conversationService.get(conversationId).subscribe({
      next: (response) => {
        this.messages = response?.messages || [];
        this.messages.forEach((m, idx) => {
          if (m.sendBy === 'AGENT') this.parseAgentMessage(m, idx);
        });
        setTimeout(() => this.scrollToBottom(), 0);
        this.renderPlotlyCharts();
      }
    });
  }

  trackByIndex(i: number): number { return i; }

  // ── Envoi d'un message ────────────────────────────────────────────────────

  sendMessage(): void {
    const question = (this.form.get('content')?.value || '').trim();

    if (!question || (!this.isStaffingAgentMode && !this.selectedProject)) return;

    this.messages.push({ content: question, sendBy: 'USER' });
    this.pendingScroll = true;
    this.cd.detectChanges();
    this.isLoading = true;

    const payload: any = {
      content: question,
      project: this.isStaffingAgentMode ? 'staffing' : this.selectedProject
    };

    if (this.conversation?.id) {
      payload['conversation'] = { id: this.conversation.id };
    }

    this.conversationService.send(payload).subscribe({
      next: (res) => {
        this.isLoading = false;

        // ── DIAGNOSTIC DE LA RÉPONSE ASSISTANT ──
        console.log('--- DIAGNOSTIC DE LA RÉPONSE ASSISTANT ---');
        console.log('Réponse brute reçue de Spring Boot:', res);
        console.log('Sources détectées dans res:', res?.sources);

        if (!this.conversation?.id && res?.conversation) {
          this.conversation = res.conversation;
          this.conversationCreated.emit(this.conversation);
        }

        // Initialisation de l'objet avec le contenu et conservation explicite des sources reçues
        let msg: any = {
          content: res?.content || '',
          sendBy: 'AGENT',
          sources: res?.sources || [],
          charts: res?.charts || []
        };

        // Traitement par parseAgentMessage
        msg = this.parseAgentMessage(msg, this.messages.length);

        console.log('Message final après traitement (parseAgentMessage):', msg);

        this.messages.push(msg);
        this.pendingScroll = true;
        this.cd.detectChanges();
        this.renderPlotlyCharts();
      },
      error: (err) => {
        console.error('Erreur lors de l\'appel de l\'assistant:', err);
        this.isLoading = false;
      }
    });

    this.form.reset();
    this.resetTextareaHeight();
  }

  private resetTextareaHeight(): void {
    const textarea = document.querySelector('textarea[formControlName="content"]') as HTMLTextAreaElement;
    if (textarea) {
      textarea.style.height     = '42px';
      textarea.style.overflowY  = 'hidden';
    }
  }

  // ── Copie ─────────────────────────────────────────────────────────────────

  copyMessage(text: string): void {
    const selBox = document.createElement('textarea');
    Object.assign(selBox.style, { position: 'fixed', left: '0', top: '0', opacity: '0' });
    selBox.value = new DOMParser().parseFromString(text, 'text/html').body.textContent || '';
    document.body.appendChild(selBox);
    selBox.focus();
    selBox.select();
    document.execCommand('copy');
    document.body.removeChild(selBox);
    this.alertService.successAlert();
  }

  // ── Parsing des messages agent ────────────────────────────────────────────

  private parseAgentMessage(m: any, idx: number): any {
    let payload: any = {};

    // On conserve les sources déjà extraites ou pré-assignées en mémoire
    const backupSources = m.sources || [];
    const backupCharts = m.charts || [];

    if (typeof m.content === 'object' && m.content !== null) {
      payload = m.content?.response ?? m.content ?? {};
    } else {
      try {
        const parsed = JSON.parse(m.content);
        payload = parsed?.response ?? parsed ?? {};
      } catch (e) {
        payload = { answer: m.content };
      }
    }

    const rawAnswer = payload.bot || payload.answer || '';

    // ── Conversion Markdown → HTML (résultat stocké dans m.content) ──────────
    m.content = rawAnswer
        .replace(/^## (.+)$/gm,
            '<p class="text-base font-semibold text-primary mt-4 mb-2 border-b border-border pb-1">$1</p>')
        .replace(/^### (.+)$/gm,
            '<p class="text-sm font-semibold text-mono mt-3 mb-1">$1</p>')
        .replace(/^\|(.+)\|$/gm, (line: string) => {
          if (/^[\|\s\-:]+$/.test(line)) return '';          // ligne séparatrice --- ignorée
          const cells = line.split('|').map((c: string) => c.trim()).filter(Boolean);
          return `<tr>${cells.map((c: string) =>
              `<td class="px-3 py-1.5 border border-border text-sm">${c}</td>`).join('')}</tr>`;
        })
        .replace(/(<tr>[\s\S]*?<\/tr>)+/g, (rows: string) =>
            `<div class="overflow-x-auto mt-2 mb-3">
         <table class="w-full border-collapse border border-border rounded text-sm">${rows}</table>
       </div>`)
        .replace(/^- (.+)$/gm,
            '<p class="ml-4 text-sm list-disc mb-1"> $1</p>')
        .replace(/(<p class="ml-4 text-sm list-disc mb-1"> .*?<\/p>\n?)+/g, (items: string) => {
          const cleanItems = items;
          return `<ul class="my-2 space-y-0.5 list-disc pl-5">${cleanItems.split('\n').map(i => i.trim() ? `<li class="text-sm">${i.replace(/<p.*?>|<\/p>/g, '')}</li>` : '').join('')}</ul>`;
        })
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\n{2,}/g, '<br><br>')
        .replace(/\n/g, '<br>');

    m.user = payload.user || '';

    // Fusion intelligente : Priorité au payload.sources/charts, sinon backup initial
    m.sources = payload.sources && payload.sources.length > 0 ? payload.sources : backupSources;
    m.charts = payload.charts && payload.charts.length > 0 ? payload.charts : (payload.response?.charts || backupCharts);

    const tableText = payload.table || '';
    if (tableText) {
      const { headers, rows } = this.parseMarkdownTable(tableText);
      m.tableHeaders = headers;
      m.tableRows    = rows;
      m.table        = tableText;
    }

    const graph = payload.graph;
    if (graph && typeof graph === 'object' && Object.keys(graph).length > 0) {
      m.graph = graph;
      const canvasId = `chart-${idx}`;
      setTimeout(() => {
        const ok = this.tryRenderGraph(canvasId, graph);
        if (!ok) setTimeout(() => this.tryRenderGraph(canvasId, graph), 50);
      }, 0);
    }

    return m;
  }
  // ── Table ─────────────────────────────────────────────────────────────────

  private parseMarkdownTable(table: string): { headers: string[]; rows: string[][] } {
    if (typeof table !== 'string') return { headers: [], rows: [] };
    const lines = table.split('\n').map(l => l.trim()).filter(Boolean);
    if (lines.length < 2) return { headers: [], rows: [] };
    const headers = lines[0].split('|').map(s => s.trim()).filter(Boolean);
    const body    = lines.slice(2).map(l => l.split('|').map(s => s.trim()).filter(Boolean));
    return { headers, rows: body };
  }

  copyTableMarkdown(table: string): void {
    navigator.clipboard.writeText(table || '');
  }

  downloadExcelFromMarkdown(table: string): void {
    const { headers, rows } = this.parseMarkdownTable(table);
    const data = rows.map(r => {
      const o: any = {};
      headers.forEach((h, i) => o[h] = r[i] || '');
      return o;
    });
    import('xlsx').then(xlsx => {
      const ws = xlsx.utils.json_to_sheet(data);
      const wb = xlsx.utils.book_new();
      xlsx.utils.book_append_sheet(wb, ws, 'Feuille1');
      xlsx.writeFile(wb, 'tableau.xlsx');
    });
  }

  // ── Graph ─────────────────────────────────────────────────────────────────

  private tryRenderGraph(canvasId: string, g: GraphPayload): boolean {
    const canvas = document.getElementById(canvasId) as HTMLCanvasElement | null;
    if (!canvas) return false;
    const prev = this.charts[canvasId];
    if (prev) { try { prev.destroy(); } catch {} }
    try {
      this.charts[canvasId] = new Chart(canvas, this.buildChartConfig(g));
      return true;
    } catch { return false; }
  }

  private buildChartConfig(g: GraphPayload): ChartConfiguration {
    if (g.type === 'pie') {
      const s = g.series?.[0] || { name: 'Valeurs', data: [] };
      return {
        type: 'pie',
        data: { labels: g.x || [], datasets: [{ label: s.name, data: s.data }] },
        options: { responsive: true, plugins: { title: { display: !!g.title, text: g.title || '' }, legend: { position: 'top' } } }
      };
    }
    const datasets = (g.series || []).map(s => ({ label: s.name, data: s.data }));
    return {
      type: g.type === 'line' ? 'line' : 'bar',
      data: { labels: g.x || [], datasets },
      options: {
        responsive: true,
        plugins: { title: { display: !!g.title, text: g.title || '' }, legend: { display: true } },
        scales: { y: { beginAtZero: true, title: { display: !!g.yLabel, text: g.yLabel || '' } } }
      }
    };
  }

  // ── Scroll ────────────────────────────────────────────────────────────────

  scrollToBottom(): void {
    if (!this.chatContainer) return;
    requestAnimationFrame(() => {
      setTimeout(() => {
        const el = this.chatContainer.nativeElement;
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
      }, 50);
    });
  }

  onScroll(_event: any): void { this.checkScrollPosition(); }

  checkScrollPosition(): void {
    if (!this.chatContainer) return;
    const el        = this.chatContainer.nativeElement;
    const threshold = 100;
    this.isScrolledToBottom = el.scrollHeight - el.clientHeight <= el.scrollTop + threshold;
  }

  autoResize(event: Event): void {
    const textarea  = event.target as HTMLTextAreaElement;
    const maxHeight = window.innerHeight * 0.2;
    const minHeight = window.innerHeight * 0.03;
    textarea.style.height    = 'auto';
    textarea.style.overflowY = 'hidden';
    const newHeight = Math.max(textarea.scrollHeight, minHeight);
    if (newHeight > maxHeight) {
      textarea.style.height    = `${maxHeight}px`;
      textarea.style.overflowY = 'auto';
    } else {
      textarea.style.height = `${newHeight}px`;
    }
  }

  // ── 6. NOUVELLES MÉTHODES COMPLÉMENTAIRES (MÉDIATION DES SOURCES) ───────────

  /**
   * Identifie et télécharge le document source référencé par l'IA.
   */
  downloadSourceFile(src: { fileName: string; pages?: string; extractCount: number }): void {
    if (this.downloadingSource === src.fileName) return;
    this.downloadingSource = src.fileName;

    const projectId = this.projectService.getSelectedProject()?.id;
    if (!projectId) { this.downloadingSource = null; return; }

    this.projectService.getProjectDocuments(projectId).subscribe({
      next: (docs) => {
        const found = docs.find(d => d.fileName === src.fileName);
        if (found) {
          this.downloadService.downloadById(found.id, found.fileName);
        } else {
          console.warn(`Fichier "${src.fileName}" non trouvé dans le projet`);
          alert(`Le fichier "${src.fileName}" n'est pas accessible au téléchargement.`);
        }
        setTimeout(() => { this.downloadingSource = null; }, 2000);
      },
      error: () => { this.downloadingSource = null; }
    });
  }

  /**
   * Fournit l'icône de l'extension associée pour l'affichage graphique des sources
   */
  getFileIcon(fileName: string): string {
    const ext = fileName?.split('.').pop()?.toLowerCase();
    const icons: Record<string, string> = {
      pdf:  'ki-file-pdf',
      doc:  'ki-file-doc',
      docx: 'ki-file-doc',
      xlsx: 'ki-file-sheet',
      xls:  'ki-file-sheet',
      xlsm: 'ki-file-sheet',
      csv:  'ki-file-binary',
    };
    return icons[ext || ''] || 'ki-file';
  }

  private renderPlotlyCharts(): void {
    const Plotly = (window as any).Plotly;
    if (!Plotly) {
      console.warn('Plotly.js is not loaded yet via CDN');
      return;
    }

    setTimeout(() => {
      this.messages.forEach((m, i) => {
        if (m.charts && m.charts.length > 0) {
          m.charts.forEach((chart: any, cIdx: number) => {
            if (chart.plotly) {
              const elementId = `plotly-chart-${i}-${cIdx}`;
              const element = document.getElementById(elementId);
              if (element) {
                try {
                  const layout = {
                    ...chart.plotly.layout,
                    autosize: true,
                    width: undefined,
                    height: 300,
                    margin: { l: 40, r: 20, t: 40, b: 40 }
                  };
                  Plotly.react(element, chart.plotly.data, layout, { responsive: true, displayModeBar: false });
                } catch (e) {
                  console.error('Erreur lors du tracé Plotly:', e);
                }
              }
              
              const tableElementId = `plotly-table-chart-${i}-${cIdx}`;
              const tableElement = document.getElementById(tableElementId);
              if (tableElement) {
                try {
                  const layout = {
                    ...chart.plotly.layout,
                    autosize: true,
                    width: undefined,
                    height: 300,
                    margin: { l: 40, r: 20, t: 40, b: 40 }
                  };
                  Plotly.react(tableElement, chart.plotly.data, layout, { responsive: true, displayModeBar: false });
                } catch (e) {
                  console.error('Erreur lors du tracé Plotly sur table:', e);
                }
              }
            }
          });
        }
      });
    }, 150);
  }
}