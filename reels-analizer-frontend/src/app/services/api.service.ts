import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Post, AnalysisRequest, DrinkStats } from '../models/post.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8000'; // FastAPI backend URL'in

  constructor(private http: HttpClient) { }

  // Profil analizi
  analyzeProfile(instagramUrl: string): Observable<Post[]> {
    const request: AnalysisRequest = { instagram_url: instagramUrl };
    return this.http.post<Post[]>(`${this.apiUrl}/analyze`, request)
      .pipe(
        catchError(this.handleError)
      );
  }

  // Kullanıcı postlarını getir
  getUserPosts(username: string): Observable<Post[]> {
    return this.http.get<Post[]>(`${this.apiUrl}/posts/${username}`)
      .pipe(
        catchError(this.handleError)
      );
  }

  // İstatistikleri getir
  getDrinkStats(username: string): Observable<DrinkStats> {
    return this.http.get<DrinkStats>(`${this.apiUrl}/stats/${username}`)
      .pipe(
        catchError(this.handleError)
      );
  }

  // Hata yönetimi
  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'Bilinmeyen bir hata oluştu!';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side hata
      errorMessage = `Hata: ${error.error.message}`;
    } else {
      // Backend hata
      errorMessage = `Hata Kodu: ${error.status}\nMesaj: ${error.error.detail || error.message}`;
    }
    
    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}