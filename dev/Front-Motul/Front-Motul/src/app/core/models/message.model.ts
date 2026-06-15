export interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: Date;
    typing?: boolean;
    showActions?: boolean;
    UserProblem?: boolean;
    hideDoesntWork?: boolean;
}