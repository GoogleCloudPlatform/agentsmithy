import { Injectable } from '@angular/core';
import { HttpClient, HttpDownloadProgressEvent, HttpEvent, HttpEventType, HttpHeaders } from '@angular/common/http';
import { Observable, Subject, tap } from 'rxjs';
import { CreateChatRequest } from '../models/chat.model';
import { environment } from 'src/environments/environment';
import { SessionService } from './user/session.service';

const chatsUrl = `${environment.backendURL}/chats`;

@Injectable({
  providedIn: 'root'
})
export class ChatService {

  constructor(private http: HttpClient, private sessionService: SessionService) {}

  postChat(query: string): Observable<HttpEvent<string>> {
    if (!this.sessionService.getSession()) {
      this.sessionService.createSession();
    }

    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });

    query = query.replace(/\s+/g, " ").trim();
    const body: CreateChatRequest = {
      input: {
        messages: [
          {
            content: query,
            type: "human",
          }
        ],
        session_id: this.sessionService.getSession()!,
      },
    };

    return this.http
      .post(chatsUrl, body, {
        headers,
        observe: "events",
        responseType: "text",
        reportProgress: true,
      })
  }
}
