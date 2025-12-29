import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent {
  instagramUrl: string = '';
  isLoading: boolean = false;
  errorMessage: string = '';

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  analyzeProfile() {
    // Validation
    if (!this.instagramUrl.trim()) {
      this.errorMessage = 'Please enter an Instagram profile link.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.apiService.analyzeProfile(this.instagramUrl).subscribe({
      next: (posts) => {
        console.log('Analiz tamamlandı:', posts);
        // Username'i URL'den çıkar ve results sayfasına git
        const username = this.extractUsername(this.instagramUrl);
        this.router.navigate(['/results', username]);
      },
      error: (error) => {
        this.errorMessage = error.message;
        this.isLoading = false;
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }

  private extractUsername(url: string): string {
    const match = url.match(/instagram\.com\/([a-zA-Z0-9._]+)/);
    if (match) {
      return match[1];
    }
    return url.replace('@', '').trim();
  }

  useExampleProfile() {
    this.instagramUrl = 'https://www.instagram.com/kitsune.cim';
  }
}