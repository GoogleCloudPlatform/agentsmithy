export type CreateChatRequest = {
    input: Input,
}

type Input = {
    messages: Message[],
    session_id: string,
}

type Message = {
    content: string,
    type: string,
}

export type Chat = {
    id: string,
    question: string,
    answer: string,
    suggested_questions: string[],
}

export type DialogQuestion = {
    questionId: string,
    questionText: string,
    hasChip: boolean,
    options: string[],
    questionSequence: string,
    answer: string
}

export type ChatEvent = {
    event: string,
    data: ChatEventData
}

type ChatEventData = {
    run_id: string
    chunk?: Chunk
}

type Chunk = {
    content: string
}