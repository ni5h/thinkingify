import { Injectable, computed, inject } from '@angular/core';
import { HttpClient, httpResource } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { ChildSummary, FamilyLink, FamilyLinksOut, TargetRole } from '../models/family';
import { ContentListItem } from '../models/content';
import { ParentReport } from '../models/parent-report';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class FamilyService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);

  readonly linksResource = httpResource<FamilyLinksOut>(() =>
    this.auth.isAuthenticated() ? '/api/v1/family/links' : undefined
  );
  readonly incomingResource = httpResource<FamilyLink[]>(() =>
    this.auth.isAuthenticated() ? '/api/v1/family/requests/incoming' : undefined
  );
  readonly outgoingResource = httpResource<FamilyLink[]>(() =>
    this.auth.isAuthenticated() ? '/api/v1/family/requests/outgoing' : undefined
  );

  readonly links = this.linksResource.value;
  readonly incoming = this.incomingResource.value;
  readonly outgoing = this.outgoingResource.value;

  // Whether the current user has at least one accepted guardian — used by
  // the Writing Studio / Studio post editor in a later phase to decide
  // whether "Publish" should mean self-publish or submit-for-approval.
  readonly hasAcceptedGuardian = computed(() => (this.links()?.as_child ?? []).length > 0);

  private reloadAll(): void {
    this.linksResource.reload();
    this.incomingResource.reload();
    this.outgoingResource.reload();
  }

  async sendRequest(email: string, targetRole: TargetRole): Promise<FamilyLink> {
    const result = await firstValueFrom(
      this.http.post<FamilyLink>('/api/v1/family/requests', { email, target_role: targetRole })
    );
    this.reloadAll();
    return result;
  }

  async accept(linkId: string): Promise<void> {
    await firstValueFrom(this.http.post(`/api/v1/family/requests/${linkId}/accept`, {}));
    this.reloadAll();
  }

  async decline(linkId: string): Promise<void> {
    await firstValueFrom(this.http.post(`/api/v1/family/requests/${linkId}/decline`, {}));
    this.reloadAll();
  }

  async unlink(linkId: string): Promise<void> {
    await firstValueFrom(this.http.delete(`/api/v1/family/links/${linkId}`));
    this.reloadAll();
  }

  async childSummary(childId: string): Promise<ChildSummary> {
    return await firstValueFrom(this.http.get<ChildSummary>(`/api/v1/family/children/${childId}/summary`));
  }

  async childContent(childId: string): Promise<ContentListItem[]> {
    return await firstValueFrom(this.http.get<ContentListItem[]>(`/api/v1/family/children/${childId}/content`));
  }

  async childReports(childId: string): Promise<ParentReport[]> {
    return await firstValueFrom(this.http.get<ParentReport[]>(`/api/v1/family/children/${childId}/reports`));
  }

  async childReport(childId: string, reportId: string): Promise<ParentReport> {
    return await firstValueFrom(
      this.http.get<ParentReport>(`/api/v1/family/children/${childId}/reports/${reportId}`)
    );
  }
}
