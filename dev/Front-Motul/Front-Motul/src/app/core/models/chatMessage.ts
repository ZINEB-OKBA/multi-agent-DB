import {GraphPayload} from "./GraphPayload";

export interface ChatMessage {
    user: string;
    bot: string;
    table: string;
    tableHeaders?: string[];
    tableRows?: string[][];
    graph?: GraphPayload;
}
