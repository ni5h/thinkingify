import { Injectable, inject } from '@angular/core';
import { HttpClient, httpResource } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { MathAttempt, MathCoachMessage, MathProblemDetail, MathProblemListItem } from '../models/math';

/**
 * Published problems via httpResource() (mirrors TopicService); the coach
 * chat + answer attempts are imperative async (mirrors CompanionService),
 * since the solver page owns their lifecycle.
 */
@Injectable({ providedIn: 'root' })
export class MathService {
  private readonly http = inject(HttpClient);

  readonly publishedResource = httpResource<MathProblemListItem[]>(() => '/api/v1/math/problems/published');
  readonly published = this.publishedResource.value;

  async getPublishedBySlug(slug: string): Promise<MathProblemDetail | undefined> {
    try {
      return await firstValueFrom(this.http.get<MathProblemDetail>(`/api/v1/math/problems/published/${slug}`));
    } catch {
      return undefined;
    }
  }

  async listCoachMessages(problemId: string): Promise<MathCoachMessage[]> {
    return firstValueFrom(this.http.get<MathCoachMessage[]>(`/api/v1/math/problems/${problemId}/coach/messages`));
  }

  async sendCoachMessage(problemId: string, body: string, sessionId: string): Promise<MathCoachMessage> {
    return firstValueFrom(
      this.http.post<MathCoachMessage>(`/api/v1/math/problems/${problemId}/coach/messages`, {
        body,
        session_id: sessionId,
      })
    );
  }

  async submitAttempt(problemId: string, submittedAnswer: string): Promise<MathAttempt> {
    return firstValueFrom(
      this.http.post<MathAttempt>(`/api/v1/math/problems/${problemId}/attempts`, {
        submitted_answer: submittedAnswer,
      })
    );
  }
}
