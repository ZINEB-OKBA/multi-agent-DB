import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
    name: 'extractDate'
})
export class ExtractDatePipe implements PipeTransform {

    transform(filename: string | null | undefined): string | null {
        if (!filename) {
            return null;
        }

        const match = filename.match(/\d{2}-\d{2}-\d{4}/);

        return match ? match[0] : null;
    }
}