/**
 * Modern TypeScript API Client with exponential backoff retry policies.
 */

export interface AuthResponse {
  accessToken: string;
  refreshToken?: string;
  expiresIn: number;
  scope: string;
}

export type TokenPair = {
  access: string;
  refresh: string;
};

export class ApiClient {
  private endpoint: string;
  private timeoutMs: number;
  private headers: Record<string, string>;

  constructor(endpoint: string, timeoutMs: number = 5000) {
    this.endpoint = endpoint.replace(/\/$/, "");
    this.timeoutMs = timeoutMs;
    this.headers = {
      "Content-Type": "application/json",
      "X-Client-Version": "1.0.0",
    };
  }

  export async function fetchWithRetry(url: string, retries: number): Promise<Response> {
    let lastError: Error | null = null;
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const res = await fetch(url);
        if (res.ok) return res;
      } catch (err: any) {
        lastError = err;
        await new Promise((r) => setTimeout(r, 100 * Math.pow(2, attempt)));
      }
    }
    throw lastError || new Error("Failed after retries");
  }
}
