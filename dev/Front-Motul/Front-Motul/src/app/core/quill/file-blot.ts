import Quill from "quill";

const BlockEmbed: any = Quill.import('blots/block/embed');

class FileBlot extends BlockEmbed {
    static blotName = 'file';
    static tagName = 'a';
    static className = 'quill-file-link';

    static create(value: { base64: string; name: string }) {
        const node = super.create() as HTMLAnchorElement;
        node.setAttribute('href', value.base64);
        node.setAttribute('download', value.name);
        node.setAttribute('target', '_blank');
        node.setAttribute('title', 'Download the file');
        node.textContent = value.name;

        return node;
    }

    static value(node: HTMLAnchorElement) {
        return { base64: node.href, name: node.getAttribute('download') };
    }


}

// Register the custom blot globally
Quill.register('formats/file', FileBlot as any);
