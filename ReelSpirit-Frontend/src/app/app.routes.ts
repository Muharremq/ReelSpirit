import { Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';
import { ResultsComponent } from './components/results/results.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'results/:username', component: ResultsComponent },
  { path: '**', redirectTo: '' }
];