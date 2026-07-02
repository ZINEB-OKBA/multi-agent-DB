export class PageModel<T = any> {
    page: number = 0;
    size: number = 10;
    sortable?: boolean = false;
    column?: string;
    direction?: string;

    // On utilise le type générique T au lieu de any
    content: T[] = [];
    totalElements: number = 0;
    totalPages: number = 0;

    constructor(page?: number) {
        this.page = page ? page : 0;
    }
}