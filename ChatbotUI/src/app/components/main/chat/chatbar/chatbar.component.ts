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
import { Component, EventEmitter, Output, OnDestroy } from '@angular/core';
import { ChatService } from 'src/app/services/chat.service';
import { UserService } from 'src/app/services/user/user.service';
import { BroadcastService } from 'src/app/services/broadcast.service';
import { last, Observable, ReplaySubject, single, Subject } from 'rxjs';
import { MatDialog } from '@angular/material/dialog';
import { Chat, ChatEvent} from 'src/app/models/chat.model';
import { animate, sequence, state, style, transition, trigger } from '@angular/animations';
import { SpeechToTextService } from 'src/app/services/speech-to-text';
import { Message, SuggestionData } from 'src/app/models/messegeType.model';
import { HttpDownloadProgressEvent, HttpEvent, HttpEventType } from '@angular/common/http';

@Component({
  selector: 'app-chatbar',
  templateUrl: './chatbar.component.html',
  styleUrls: ['./chatbar.component.scss'],
  animations: [
    trigger('bounce', [
      state('true', style({ transform: 'translateY(0)', color: '#4285F4' })),
      transition('* => true', [
        sequence([
          style({ transform: 'translateY(0)' }),
          animate("400ms cubic-bezier(0,0,0,1)", style({ transform: 'translateY(-14px)', color: '#4285F4' })),
          animate("300ms cubic-bezier(1,0,1,1)", style({ transform: 'translateY(0)', color: '#4285F4' })),
          animate("200ms cubic-bezier(0,0,0,1)", style({ transform: 'translateY(-10px)', color: '#4285F4' })),
          animate("150ms cubic-bezier(1,0,1,1)", style({ transform: 'translateY(0)', color: '#4285F4' })),
          animate("100ms cubic-bezier(0,0,0,1)", style({ transform: 'translateY(-5px)', color: '#4285F4' })),
          animate("80ms cubic-bezier(1,0,1,1)", style({ transform: 'translateY(0)', color: '#4285F4' })),
        ]),
      ])
    ]),
    trigger('delete', [
      state('true', style({ transform: 'translateY(0)', color: '#ed143d' })),
      transition('* => true', [
        sequence([
          style({ transform: 'translateY(0)' }),
          animate("400ms cubic-bezier(0,0,0,1)", style({ transform: 'translateX(14px)', color: '#ed143d' })),
          animate("300ms cubic-bezier(1,0,1,1)", style({ transform: 'translateX(0)', color: '#ed143d' })),
          animate("200ms cubic-bezier(0,0,0,1)", style({ transform: 'translateX(-14px)', color: '#ed143d' })),
          animate("150ms cubic-bezier(1,0,1,1)", style({ transform: 'translateX(0)', color: '#ed143d' })),
          animate("100ms cubic-bezier(0,0,0,1)", style({ transform: 'translateX(7px)', color: '#ed143d' })),
          animate("80ms cubic-bezier(1,0,1,1)", style({ transform: 'translateX(0)', color: '#ed143d' })),
        ]),
      ])
    ]),
  ]
})
export class ChatbarComponent implements OnDestroy {

  @Output() onSubmit: EventEmitter<any> = new EventEmitter();

  isSuggestedQuestion: string = '';
  chatQuery: string
  chatQuery$: Observable<Message>;
  showLoader: boolean = false;
  startTimer: boolean = false;
  conversation: Message[] = [];
  leftContainerClass = "";
  rightContainerClass = "";
  index = 2;
  loaderTextArray: string[] = [
    "I am a conversation bot built on Google Cloud's Vertex AI tools.",
    "Tool Tip: You can reset the conversation anytime using the reset button next the the text input box.",
    "Joke : Why did the robot go on a diet? Because it had too many bytes!",
    "Joke : Why can't bicycles stand up by themselves? Because they are two-tired!",
    "Joke : How does a computer get drunk? It takes screenshots."
  ];
  loaderTextTimeout: undefined | ReturnType<typeof setTimeout>;
  loaderText = "";
  loaderTextIndex = 0;
  loaderIndex = 1;
  isChatDisabled: boolean = false;
  botStartTime: number;
  initialQuestion: string;
  ticketId: string;
  categoryIntent: string = "";
  changeImageInterval: undefined | ReturnType<typeof setTimeout>;
  panelOpenState = false;
  like = false;
  dislike = false;
  response: Response
  loaderSelectedChip = '';
  showLoaderLikeDislikeButtons = false;
  outOfContextAnswerResponseObject = {
    like: false,
    dislike: false
  }
  showSuggesstion = false;
  suggestedQuestionMessage: Message;
  loader_chat_id: any;
  questionArray: any[] = [];

  /** DEP accordion border colors */
  borderColors = ['#4285F4', '#0F9D58', '#F4B400', '#DB4437'];

  private readonly destroyed = new ReplaySubject<void>(1);
  isRecording = false;
  transcribedText = '';
  mediaRecorder: MediaRecorder;
  audioChunks: Blob[] = [];

  constructor(
    public dialog: MatDialog,
    private chatService: ChatService,
    public userService: UserService,
    private broadcastService: BroadcastService,
    private speechToTextService: SpeechToTextService,
  ) {
    this.chatQuery$ = this.broadcastService.chatQuery$
    this.chatQuery$.subscribe((value: any) => {
      this.conversation.push(value);
    });
    this.loaderText = this.loaderTextArray[Math.round(Math.random() * 10)];
    this.checkIfMessege();
  }

  setupMediaRecorder(stream: MediaStream) {
    this.mediaRecorder = new MediaRecorder(stream);
    this.mediaRecorder.ondataavailable = event => this.audioChunks.push(event.data);
    this.mediaRecorder.onstop = () => this.sendAudioToGCP();
  }

  async sendAudioToGCP() {
    const audioBlob = new Blob(this.audioChunks);
    (await this.speechToTextService.transcribeAudio(audioBlob)).subscribe(
      (response: any) => {
        this.chatQuery = response[0]
      },
      (error: any) => {
      }
    );
  }

  ngOnDestroy() {
    this.destroyed.next();
    this.destroyed.complete();
  }

  getStringData(obj: any): string {
    let str = (obj as string);
    if (str === "" || str.length === 0) {
      return "Sorry! I don't have sufficient information to answer this question at the moment.";
    }
    return (obj as string);
  }


  getSuggestionData(obj: any): SuggestionData {
    return (obj as SuggestionData);
  }

  checkIfMessege() {
    if (this.conversation.length == 1 && this.conversation[0].type == 'user') {
      this.showLoader = true;
      this.setTimeoutForLoaderText();
      this.setCyclicBackgroundImages();
      this.startTimer = true;
      this.botStartTime = new Date().getTime()
      this.initialQuestion = this.conversation[0].body;
      this.pushQuestion(this.initialQuestion);
      this.chatService.postChat(this.conversation[0].body).subscribe({
        next: (event: HttpEvent<string>) => {
          if (event.type === HttpEventType.DownloadProgress) {
            this.handleBotResponse(
              (event as HttpDownloadProgressEvent).partialText + "…",
            );
          } else if (event.type === HttpEventType.Response) {
            this.handleBotResponse(event.body!);
          }
        },
        error: () => {
          console.log("Error getting stream events");
        },
      });
    }
  }

  pushQuestion(question: string, id?: any) {
    this.questionArray.push({ question, id });
  }

  assignId(id: any) {
    for (let i = 0; i < this.questionArray.length; i++) {
      if (!this.questionArray[i].id) {
        this.questionArray[i].id = id;
        break;
      }
    };
  }

  getQuestion(id: any) {
    const questionObj = this.questionArray.find(x => x.id === id);
    return questionObj?.question || '';
  }

  async submitMessage(event: any) {
    this.outOfContextAnswerResponseObject = {
      like: false,
      dislike: false
    };
    this.removeSuggestionElement();
    this.pushQuestion(this.chatQuery);

    this.botStartTime = new Date().getTime();
    // keeps the scrollbar to the bottom
    const parentElement = document.getElementsByClassName('chat-body');
    parentElement[0].scrollTo(0, parentElement[0].scrollHeight);

    if (event instanceof KeyboardEvent || event instanceof MouseEvent) {
      event.preventDefault();
    }
    if (!this.chatQuery || this.chatQuery === '') {
      return;
    }
    if (!this.initialQuestion) this.initialQuestion = this.chatQuery;

    let singleMessage: Message = {
      body: this.chatQuery,
      type: 'user',
      shareable: false,
    }

    this.conversation.unshift(singleMessage);
    this.chatQuery = '';
    this.showLoader = true;
    this.setTimeoutForLoaderText();
    this.setCyclicBackgroundImages();
    this.chatService.postChat(singleMessage.body).subscribe({
      next: (event: HttpEvent<string>) => {
        if (event.type === HttpEventType.DownloadProgress) {
          this.handleBotResponse(
            (event as HttpDownloadProgressEvent).partialText as string
          );
        } else if (event.type === HttpEventType.Response) {
          this.handleBotResponse(event.body as string);
        }
      },
      error: () => {
        console.log("Error getting stream events");
      },
    });
  }

  setErrorMessage() {
    this.clearTimeoutForLoaderText();
    this.leftContainerClass = 'left-side-container-error';
    this.loaderText = 'Oops something went wrong , please try again.';
    this.rightContainerClass = 'right-side-container-error';
    this.showLoaderLikeDislikeButtons = false;
  }

  setAnswerNotFoundText(loaderText: string) {
    this.clearTimeoutForLoaderText();
    this.showLoader = true;
    this.leftContainerClass = 'answer-not-found';
    this.rightContainerClass = 'right-side-container-error';
    this.loaderText = loaderText + " Please try asking something else";
    this.showLoaderLikeDislikeButtons = true;
  }

  stopTicketCreationFlow() {
    this.isChatDisabled = false;
    this.chatQuery = '';
  }

  setCyclicBackgroundImages() {
    if (this.loaderTextIndex == 3) {
      this.loaderTextIndex = 0;
    }
    this.leftContainerClass = 'left-side-container-' + (this.loaderTextIndex + 1);
    this.rightContainerClass = 'right-side-container-' + (this.loaderTextIndex + 1);
    this.loaderTextIndex++;
  }

  setTimeoutForLoaderText() {
    this.loaderText = this.loaderTextArray[Math.round(Math.random() * 10)];
    this.showLoaderLikeDislikeButtons = false;
    this.loaderTextTimeout = setInterval(() => { this.setCyclicLoaderText(); }, 3000);
  }

  clearTimeoutForLoaderText() {
    clearTimeout(this.loaderTextTimeout);
  }

  setCyclicLoaderText() {
    this.loaderText = this.loaderTextArray[Math.round(Math.random() * 10)];
    this.loaderIndex++;
  }

  handleBotResponse(answer: string) {
    let events: string[] = answer.split("\n");
    events.pop();
    let answerId = (JSON.parse(events[0]) as ChatEvent ).data.run_id

    if ( answerId === this.conversation[0].chat_id) {
      let lastEvent: ChatEvent = JSON.parse(events.slice(-1)[0]);
      if(lastEvent.event == "on_chat_model_stream") {
        this.conversation[0].botAnswer += lastEvent.data.chunk!.content
      }
      return;
    } 

    let response: Chat = {
      id: answerId,
      question: this.chatQuery,
      answer: "",
      suggested_questions: []
    }
    
    let endTime = new Date().getTime();
    this.assignId(response?.id);

    let singleMesage: Message = {
      body: "",
      botAnswer: response.answer,
      type: 'bot',
      responseTime: ((endTime - this.botStartTime) / 1000).toString(),
      shareable: true,
      botStartTime: this.botStartTime.toString(),
      extras: {
        like: false,
        dislike: false,
        delete: false,
      },
      chat_id: response.id!
    };

    this.conversation.unshift(singleMesage);
    this.setSuggestedQuestionInChat(response, endTime);
    this.showLoader = false;
    this.clearTimeoutForLoaderText();
    this.isSuggestedQuestion = '';
  }

  // adds Suggested question as another message
  setSuggestedQuestionInChat(response: Chat, endTime: number) {
    if (response.suggested_questions?.length || 0 > 0) {
      this.showSuggesstion = true;
      this.suggestedQuestionMessage = {
        body: "",
        type: 'bot',
        responseTime: ((endTime - this.botStartTime) / 1000).toString(),
        shareable: true,
        extras: {
          like: false,
          dislike: false
        },
        suggestedQuestion: response.suggested_questions
      }
      setTimeout(() => {
        const botResponseElement = document.getElementById(this.botStartTime.toString());
        const parentElement = document.getElementsByClassName('chat-body');
        const y = botResponseElement?.offsetTop;
        if (y) {
          parentElement[0].scroll({
            top: y - 30,
            behavior: 'smooth'
          })
        }
      }, 1000);
    }
  }

  chipControlOnSelect(event: any) {
    this.chatQuery = event.target.innerText;
    this.submitMessage(event);
  }

  getResponseforSuggestionQuery(event: any) {
    this.isSuggestedQuestion = event;
    this.chatQuery = event;
    document.querySelectorAll(".bot-suggestion-container").forEach(el => el.remove());
    this.submitMessage(event);
  }

  removeSuggestionElement() {
    this.showSuggesstion = false;
    document.querySelectorAll(".bot-suggestion-container").forEach(el => el.remove());
  }

  startRecording() {
    this.isRecording = true;
    this.audioChunks = [];
    this.mediaRecorder.start();
  }

  stopRecording() {
    this.isRecording = false;
    this.mediaRecorder.stop();
  }

}
