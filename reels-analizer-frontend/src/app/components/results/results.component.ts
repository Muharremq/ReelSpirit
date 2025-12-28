import { Component, OnInit, OnDestroy } from '@angular/core'; // <-- 1. OnDestroy EKLENDİ
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { Post, DrinkStats } from '../../models/post.model';
import { interval, Subscription } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.scss']
})
export class ResultsComponent implements OnInit, OnDestroy {
  username: string = '';
  posts: Post[] = [];
  stats: DrinkStats | null = null;
  isLoading: boolean = true;
  errorMessage: string = '';
  
  selectedCategory: string = 'all';
  filteredPosts: Post[] = [];
  availableCategories: string[] = [];
  pollingSubscription: Subscription | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService
  ) {}

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.username = params['username'];
      if (this.username) {
        this.loadData(); // <-- 2. İSİM DÜZELTİLDİ (loadPageData -> loadData)
        this.startPolling(); 
      }
    });
  }

  ngOnDestroy() {
    this.stopPolling();
  }

  startPolling() {
    this.stopPolling();

    this.pollingSubscription = interval(5000)
      .pipe(
        switchMap(() => this.apiService.getScanStatus(this.username)),
        takeWhile(response => response.status !== 'completed', true) 
      )
      .subscribe({
        next: (response) => {
          console.log('Tarama Durumu:', response.status);
          
          if (response.status === 'completed') {
            console.log('Tarama bitti! Sayfa yenileniyor...');
            this.loadData(); // <-- 2. İSİM DÜZELTİLDİ (loadPageData -> loadData)
            this.stopPolling();
          }
        },
        error: (err) => console.error('Polling hatası:', err)
      });
  }

  stopPolling() {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
      this.pollingSubscription = null;
    }
  }

  // Fonksiyonun orijinal ismi bu, yukarıdaki çağrıları buna uydurduk.
  loadData() {
    this.isLoading = true;
    this.errorMessage = '';

    Promise.all([
      this.apiService.getUserPosts(this.username).toPromise(),
      this.apiService.getDrinkStats(this.username).toPromise()
    ]).then(([posts, stats]) => {
      this.posts = posts || [];
      this.stats = stats || null;
      this.filteredPosts = this.posts;
      this.extractCategories();
      this.isLoading = false;
    }).catch(error => {
      this.errorMessage = 'An error occurred while loading the data: ' + error.message;
      this.isLoading = false;
    });
  }

  extractCategories() {
    const categories = new Set<string>();
    this.posts.forEach(post => {
      if (post.drink_category && post.drink_category !== 'None' && post.drink_category !== 'Yok') {
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

  getCategoryColor(category: string | null): string {
    // 3. MANTIK DÜZELTİLDİ: 'Other' buraya takılmasın diye çıkardık.
    // Eğer buraya 'Other' yazarsan aşağıdaki haritaya bakmaz, gri döner.
    if (!category || category === 'Yok') return '#6b7280';
    
    const colorMap: { [key: string]: string } = {
      'Whisky': '#d97706',
      'Whisky Cocktail': '#f59e0b',
      'Rum': '#92400e',
      'Rum Cocktail': '#b45309',
      'Gin': '#059669',
      'Gin Cocktail': '#10b981',
      'Vodka': '#0891b2',
      'Vodka Cocktail': '#06b6d4',
      'Tequila': '#84cc16',
      'Tequila Cocktail': '#a3e635',
      'Liqueur': '#8b5cf6',
      'Liqueur Cocktail': '#a78bfa',
      'Coffee Cocktail': '#78350f',
      'Mixed Cocktail': '#ec4899',
      'Wine': '#7c2d12',
      'Beer': '#fbbf24',
      'Rakı': '#cbd5e1',
      'Other': '#9ca3af'
    };
    
    return colorMap[category] || '#6b7280';
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  }

  getMediaIcon(mediaType: string): string {
    return mediaType === 'VIDEO' ? '🎥' : '📷';
  }

  getInstagramPostUrl(post: Post): string {
    if (post.permalink) {
      return post.permalink;
    }
    return `https://www.instagram.com/p/${post.instagram_id}/`;
  }
}