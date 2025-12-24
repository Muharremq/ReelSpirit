import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { Post, DrinkStats } from '../../models/post.model';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.scss']
})
export class ResultsComponent implements OnInit {
  username: string = '';
  posts: Post[] = [];
  stats: DrinkStats | null = null;
  isLoading: boolean = true;
  errorMessage: string = '';
  
  // Filtreleme için
  selectedCategory: string = 'all';
  filteredPosts: Post[] = [];
  
  // Kategoriler
  availableCategories: string[] = [];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService
  ) {}

  ngOnInit() {
    // URL'den username'i al
    this.route.params.subscribe(params => {
      this.username = params['username'];
      this.loadData();
    });
  }

  loadData() {
    this.isLoading = true;
    this.errorMessage = '';

    // Postları ve istatistikleri paralel olarak yükle
    Promise.all([
      this.apiService.getUserPosts(this.username).toPromise(),
      this.apiService.getDrinkStats(this.username).toPromise()
    ]).then(([posts, stats]) => {
      this.posts = posts || [];
      this.stats = stats || null;
      this.filteredPosts = this.posts;
      
      // Kategorileri çıkar
      this.extractCategories();
      
      this.isLoading = false;
    }).catch(error => {
      this.errorMessage = 'Veriler yüklenirken bir hata oluştu: ' + error.message;
      this.isLoading = false;
    });
  }

  extractCategories() {
    const categories = new Set<string>();
    this.posts.forEach(post => {
      if (post.drink_category && post.drink_category !== 'Yok') {
        categories.add(post.drink_category);
      }
    });
    this.availableCategories = Array.from(categories).sort();
  }

  filterByCategory(category: string) {
    this.selectedCategory = category;
    
    if (category === 'all') {
      this.filteredPosts = this.posts;
    } else {
      this.filteredPosts = this.posts.filter(post => 
        post.drink_category === category
      );
    }
  }

  goBack() {
    this.router.navigate(['/']);
  }

  // Kategori rengini belirle
  getCategoryColor(category: string | null): string {
    if (!category || category === 'Yok') return '#6b7280';
    
    const colorMap: { [key: string]: string } = {
      'Viski': '#d97706',
      'Viski Kokteyli': '#f59e0b',
      'Rom': '#92400e',
      'Rom Kokteyli': '#b45309',
      'Cin': '#059669',
      'Cin Kokteyli': '#10b981',
      'Votka': '#0891b2',
      'Votka Kokteyli': '#06b6d4',
      'Tekila': '#84cc16',
      'Tekila Kokteyli': '#a3e635',
      'Likör': '#8b5cf6',
      'Likör Kokteyli': '#a78bfa',
      'Kahve Kokteyli': '#78350f',
      'Karışık Kokteyl': '#ec4899',
      'Şarap': '#7c2d12',
      'Bira': '#fbbf24',
      'Rakı': '#cbd5e1'
    };
    
    return colorMap[category] || '#6b7280';
  }

  // Tarih formatla
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  // Post türü ikonu
  getMediaIcon(mediaType: string): string {
    return mediaType === 'VIDEO' ? '🎥' : '📷';
  }

  // Instagram post URL'ini oluştur
getInstagramPostUrl(postId: string): string {
  return `https://www.instagram.com/p/${postId}/`;
}
}