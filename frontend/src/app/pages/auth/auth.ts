import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth.html',
  styleUrl: './auth.scss'
})
export class Auth {
  mode: 'login' | 'register' = 'login';
  email = '';
  password = '';
  displayName = '';
  loading = false;
  errorMessage = '';

  constructor(private authService: AuthService, private router: Router) { }

  submit(): void {
    if (this.loading) return;
    this.errorMessage = '';
    this.loading = true;
    const request = this.mode === 'login'
      ? this.authService.login(this.email, this.password)
      : this.authService.register(this.email, this.password, this.displayName);

    request.subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: err => {
        this.loading = false;
        this.errorMessage = err?.error?.message || err?.message || 'Authentication failed.';
      }
    });
  }

  toggleMode(): void {
    this.mode = this.mode === 'login' ? 'register' : 'login';
    this.errorMessage = '';
  }
}
