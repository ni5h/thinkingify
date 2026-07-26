import { Injectable, inject } from '@angular/core';
import { HttpClient, httpResource } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { ProfileUpdate, UserLinkedProfile, UserProfile } from '../models/user';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class UserProfileService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);

  readonly meResource = httpResource<UserProfile>(() =>
    this.auth.isAuthenticated() ? '/api/v1/auth/me' : undefined
  );
  readonly me = this.meResource.value;

  async update(changes: ProfileUpdate): Promise<UserProfile> {
    const result = await firstValueFrom(this.http.patch<UserProfile>('/api/v1/auth/me', changes));
    this.meResource.reload();
    return result;
  }

  async uploadAvatar(blob: Blob): Promise<string> {
    const formData = new FormData();
    formData.append('file', blob, 'avatar.jpg');
    const response = await firstValueFrom(
      this.http.post<{ url: string }>('/api/v1/uploads/avatar', formData)
    );
    return response.url;
  }

  async linkedProfile(userId: string): Promise<UserLinkedProfile> {
    return await firstValueFrom(this.http.get<UserLinkedProfile>(`/api/v1/users/${userId}/profile`));
  }
}
