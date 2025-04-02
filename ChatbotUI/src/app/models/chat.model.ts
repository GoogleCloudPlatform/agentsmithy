// Copyright 2025 Google LLC. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
export type CreateChatRequest = {
    input: Input,
}

type Input = {
    input: {
        messages: Message[],
        session_id: string,
    }
}

export type Message = {
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