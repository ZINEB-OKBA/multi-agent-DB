import * as XLSX from "xlsx";

const getFileName = (name: string) => {
    let timeSpan = new Date().toISOString();
    let sheetName = name || "ExportResult";
    let fileName = `${sheetName}-${timeSpan}`;
    return {
        sheetName,
        fileName
    };
};
export class ExportHelper {
    static exportTableToExcel(tableId: string, name?: string) {
        let { sheetName, fileName } = getFileName(name);
        let targetTableElm = document.getElementById(tableId);
        let wb = XLSX.utils.table_to_book(targetTableElm, <XLSX.Table2SheetOpts>{
            sheet: sheetName
        });
        XLSX.writeFile(wb, `${fileName}.xlsx`);
    }

    static exportArrayToExcel(data: any[], name?: string, headerInfo?: string) {
        let { sheetName, fileName } = getFileName(name);

        let wb = XLSX.utils.book_new();
        let ws = XLSX.utils.aoa_to_sheet([]);

        if (headerInfo) {
            XLSX.utils.sheet_add_aoa(ws, [[headerInfo]], { origin: 'A1' });
        }

        XLSX.utils.sheet_add_json(ws, data, { origin: 'A1' });

        XLSX.utils.book_append_sheet(wb, ws, sheetName);

        XLSX.writeFile(wb, `${fileName}.xlsx`);
    }
}
