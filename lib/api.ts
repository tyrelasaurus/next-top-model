import { Team, Game, Player, SearchFilters } from '@/types/sports';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Team endpoints
  async getTeams(params?: { league?: string; city?: string; name?: string }): Promise<Team[]> {
    const searchParams = new URLSearchParams();
    if (params?.league) searchParams.append('league', params.league);
    if (params?.city) searchParams.append('city', params.city);
    if (params?.name) searchParams.append('name', params.name);
    
    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request<Team[]>(`/api/v1/teams/${query}`);
  }

  async getTeam(teamUid: string): Promise<Team> {
    return this.request<Team>(`/api/v1/teams/${teamUid}`);
  }

  // Game endpoints (placeholder for when we implement them)
  async getGames(filters?: SearchFilters): Promise<Game[]> {
    // TODO: Implement when games API is ready
    throw new Error('Games API not implemented yet');
  }

  // Player endpoints (placeholder)
  async getPlayers(teamUid?: string): Promise<Player[]> {
    // TODO: Implement when players API is ready
    throw new Error('Players API not implemented yet');
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }
}

export const apiClient = new ApiClient();
export default apiClient;