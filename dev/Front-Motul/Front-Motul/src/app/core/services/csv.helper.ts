import { Injectable } from '@angular/core';

type Delimiter = ',' | ';' | '\t';

export interface CsvOptions<T> {
    filename?: string;                 // without extension
    delimiter?: Delimiter;             // default: ','
    includeHeader?: boolean;           // default: true
    bom?: boolean;                     // default: true (helps Excel)
    headers?: string[];                // header order/labels (dot paths allowed)
    mapRow?: (row: T) => Record<string, any>; // pick/rename fields
    eol?: '\r\n' | '\n';               // default: '\r\n' for Excel
}

@Injectable({ providedIn: 'root' })
export class CsvService {
    download<T extends Record<string, any>>(rows: T[], opts: CsvOptions<T> = {}): void {
        if (!rows?.length) return;

        const delimiter: Delimiter = opts.delimiter ?? ',';
        const eol = opts.eol ?? '\r\n';
        const includeHeader = opts.includeHeader ?? true;
        const bom = opts.bom ?? true;
        const filename = (opts.filename ?? 'export')+Date.now().toString() + '.csv';

        // Optionally reshape each row (select/rename fields)
        const shaped = opts.mapRow ? rows.map(r => opts.mapRow!(r)) : rows;

        // Flatten nested objects so "user.name" works
        const flat = shaped.map(r => this.flatten(r));

        // Determine headers/order
        const headerSet = new Set<string>();
        flat.forEach(r => Object.keys(r).forEach(k => headerSet.add(k)));

        const headers = (opts.headers && opts.headers.length)
            ? opts.headers
            : Array.from(headerSet);

        // Build CSV
        const lines: string[] = [];

        if (includeHeader) {
            lines.push(headers.map(h => this.escapeCell(h, delimiter)).join(delimiter));
        }

        for (const row of flat) {
            const cells = headers.map(h => this.escapeCell(this.getByPath(row, h), delimiter));
            lines.push(cells.join(delimiter));
        }

        const csv = (bom ? '\uFEFF' : '') + lines.join(eol);
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    }

    // --- helpers ---

    private flatten(obj: Record<string, any>, prefix = ''): Record<string, any> {
        const out: Record<string, any> = {};
        for (const [k, v] of Object.entries(obj)) {
            const key = prefix ? `${prefix}.${k}` : k;
            if (v !== null && typeof v === 'object' && !Array.isArray(v) && !(v instanceof Date)) {
                Object.assign(out, this.flatten(v, key));
            } else {
                out[key] = v;
            }
        }
        return out;
    }

    private getByPath(obj: Record<string, any>, path: string): any {
        // path is already flattened key; just return or empty
        return obj[path] ?? '';
    }

    private escapeCell(value: any, delimiter: Delimiter): string {
        if (value === null || value === undefined) return '';
        let s = String(value);

        // Normalize newlines
        s = s.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

        const mustQuote = s.includes('"') || s.includes('\n') || s.includes(delimiter);
        if (s.includes('"')) s = s.replace(/"/g, '""'); // escape quotes

        return mustQuote ? `"${s}"` : s;
    }
}
