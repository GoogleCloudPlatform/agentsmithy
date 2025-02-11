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
import { Component, TemplateRef, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { BroadcastService } from 'src/app/services/broadcast.service';
import { UntypedFormGroup, UntypedFormBuilder } from '@angular/forms';
import { UserService } from 'src/app/services/user/user.service';
import { Message } from 'src/app/models/messegeType.model';
import { SessionService } from 'src/app/services/user/session.service';
import { MatDialog } from '@angular/material/dialog';
import { ReplaySubject } from 'rxjs';
import { MatSnackBar } from '@angular/material/snack-bar';
import { animate, sequence, state, style, transition, trigger } from '@angular/animations';
import { SpeechToTextService } from '../../services/speech-to-text';

@Component({
  selector: 'app-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss'],
  animations: [
    trigger('scale', [
      state('true', style({ transform: 'translateY(0)', color: '#4285F4' })),
      transition('* => true', [
        sequence([
          style({ transform: 'translateY(0)' }),
          animate("450ms cubic-bezier(0,0,0,1)", style({ transform: 'scale(0.8)', color: '#4285F4' })),
          animate("400ms cubic-bezier(1,0,1,1)", style({ transform: 'scale(1.2)', color: '#4285F4' })),
          animate("350ms cubic-bezier(1,0,1,1)", style({ transform: 'scale(0.8)', color: '#4285F4' })),
          animate("250ms cubic-bezier(0,0,0,1)", style({ transform: 'scale(1)', color: '#4285F4' })),
          animate("200ms cubic-bezier(0,0,0,1)", style({ transform: 'scale(-1,1)', color: '#4285F4' })),
          animate("150ms cubic-bezier(1,0,1,1)", style({ transform: 'scale(-1,1)', color: '#4285F4' })),
        ]),
      ])
    ])
  ]
})
export class MainComponent {
  hasPermission: boolean = false;
  permissionRequested: boolean = false;
  stream: MediaStream | null = null; // Store the stream
  isRecording = false;
  
  transcribedText = '';
  mediaRecorder: MediaRecorder;
  audioChunks: Blob[] = [];

  searchForm: UntypedFormGroup
  selectedType: string = 'chat';
  chatQuery: string = '';
  chipSelected: string = '';
  allQuestions: Map<string, string[]> = new Map()
  onHover: boolean = false;
  savedUser;
  lastExpandedElement: string = '';
  showTos = false;
  showBadge = false;
  tooltipTextList: string[] = [];

  @ViewChild('userBadgeTemplate', { static: true })
  userBadgeTemplate!: TemplateRef<{}>;

  intentSelected: boolean;
  dialogRef: any;

  private readonly destroyed = new ReplaySubject<void>(1);
  toolTipText: string | undefined;
  tooltipTextTimeout: undefined | ReturnType<typeof setTimeout>;
  createIntentComponentInstance:any;


  constructor(private router: Router,
    private broadcastService: BroadcastService,
    private fb: UntypedFormBuilder,
    private sessionService: SessionService,
    public userService: UserService,
    public dialog: MatDialog,
    private _snackBar: MatSnackBar,
    private speechToTextService: SpeechToTextService,
  ) {
    this.searchForm = this.fb.group({
      searchTerm: this.fb.control('')
    });
    this.savedUser = userService.getUserDetails();
    this.sessionService.createSession();
    this.setTimeoutForToolTipText();
  }

  navigate() {
    let userMessage: Message = {
      body: this.chatQuery,
      type: 'user',
      shareable: false,
    }
    this.chatQuery && this.broadcastService.nextChatQuery(userMessage);
    this.router.navigateByUrl('/' + this.selectedType);
  };

  changeSelectedAssistance(assistantType: string) {
    this.selectedType = assistantType;
  }

  removeIntentSelection() {
    this.chipSelected = '';
  }

  assignQToChatQuery(question: string) {
    this.chatQuery = question;
    let userMessage: Message = {
      body: this.chatQuery,
      type: 'user',
      shareable: false,
    }
    this.chatQuery && this.broadcastService.nextChatQuery(userMessage);
    this.router.navigateByUrl('/' + this.selectedType);
  }

  showFullButton() {
    this.onHover = true;
  }
  hideFullButton() {
    this.onHover = false;
  }

  getHumanReadablestring(s: string) {
    return s.replace("_", " ").replace(/(^\w{1})|(\s+\w{1})/g, letter => letter.toUpperCase());
  }

  scrollToSelectedElement(classNameToFilterElement: string) {
    const childElement = document.getElementById(classNameToFilterElement);
    childElement?.scrollIntoView();
  }

  openSnackBar(message: string, color: string) {
    this._snackBar.open(message, 'Close', {
      panelClass: [color],
      horizontalPosition: 'end',
      verticalPosition: 'top',
      duration: 3000,
    });
  }

  ngOnInit() {
    this.checkMicPermission(); 
  }

  ngOnDestroy() {
    this.destroyed.next();
    this.destroyed.complete();
    if (this.stream) {
      this.stopStream(); // Stop the stream when component is destroyed
    }
  }

  async checkMicPermission() {
    try {
      const permissionStatus = await navigator.permissions.query({ name: 'microphone' as PermissionName });
      this.hasPermission = permissionStatus.state === 'granted';

      permissionStatus.onchange = () => { // Listen for permission changes
        this.hasPermission = permissionStatus.state === 'granted';
      };

    } catch (error) {
      console.error('Error checking microphone permission:', error);
    }
  }

  startStream() {
    if (this.stream) return; // Stream already running
    this.isRecording = true;
    navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
      this.stream = stream;
      console.log('Microphone stream started:', this.stream);
      // ... any other actions with stream ...
    })
    .catch(err => {
      console.error('Error starting stream:', err);
      this.hasPermission = false; // Ensure to update permission status
    });
  }

  stopStream() {
    if (this.stream) {
      this.isRecording = false;
      const tracks = this.stream.getAudioTracks();
      tracks.forEach(track => track.stop());
      this.stream = null;
      console.log('Microphone stream stopped.');
    }
  }

  async requestMicPermission() {
    this.permissionRequested = true; // Set flag to indicate request was made
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.hasPermission = true;
      this.permissionRequested = false; // Reset flag
      // Now you can use the microphone stream (this.stream)
      console.log('Microphone stream granted:', this.stream);
    } catch (error) {
      this.hasPermission = false;
      console.error('Error getting microphone permission:', error);
    }
  }

  setupMediaRecorder(stream: MediaStream) {
    this.mediaRecorder = new MediaRecorder(stream);
    this.mediaRecorder.ondataavailable = event => this.audioChunks.push(event.data);
    this.mediaRecorder.onstop = () => this.sendAudioToGCP();
  }

  async sendAudioToGCP() {
    const audioBlob = new Blob(this.audioChunks);
    // console.log(audioBlob);
    (await this.speechToTextService.transcribeAudio(audioBlob)).subscribe(
      (response: any) => {
        // console.log(response)
        this.chatQuery = response[0]
      },
      (error: any) => {
        // Handle errors
      }
    );
  }

  setTimeoutForToolTipText() {
    if (!window.localStorage['showTooltip']) {
      this.toolTipText = this.tooltipTextList[Math.floor(Math.random() * this.tooltipTextList.length)];
      this.tooltipTextTimeout = setInterval(() => { this.toolTipText = this.tooltipTextList[Math.floor(Math.random() * this.tooltipTextList.length)]; }, 7000);
    }
  }

  dismissToolTip() {
    window.localStorage['showTooltip'] = true;
    this.toolTipText = undefined;
    clearTimeout(this.tooltipTextTimeout);
  }

}
