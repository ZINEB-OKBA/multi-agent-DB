import Quill from 'quill';
import "./file-blot";
const icons = Quill.import('ui/icons');
icons['file'] = '<i class="ki-filled ki-add-files"></i>';



export const quillModules = (fileHandler: () => void) => ({
    toolbar: {
        container: [
            // Text styling
            ['bold', 'italic', 'underline', 'strike'],

            // Headings / fonts
            [{ header: [1, 2, 3, 4, 5, 6, false] }],
            [{ font: [] }],
            [{ size: ['small', false, 'large', 'huge'] }],

            // Colors & background
            [{ color: [] }, { background: [] }],

            // Lists & indentation
            [{ list: 'ordered' }, { list: 'bullet' }],
            [{ indent: '-1' }, { indent: '+1' }],

            // Alignment
            [{ align: [] }],

            // Links, images, files, code
            ['link', 'file', 'code-block'],

            // Clean formatting
            ['clean']
        ],
        theme: 'snow',
        handlers: {
            file: fileHandler,
        }
    }
});
