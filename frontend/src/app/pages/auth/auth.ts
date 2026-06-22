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

    const validationError = this.validateForm();
    if (validationError) {
      this.errorMessage = validationError;
      return;
    }

    this.loading = true;
    const request = this.mode === 'login'
      ? this.authService.login(this.email.trim(), this.password)
      : this.authService.register(this.email.trim(), this.password, this.displayName.trim());

    request.subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: err => {
        this.loading = false;
        this.errorMessage = this.extractErrorMessage(err);
      }
    });
  }

  toggleMode(): void {
    this.mode = this.mode === 'login' ? 'register' : 'login';
    this.errorMessage = '';
  }

  private validateForm(): string | null {
    const email = this.email.trim();
    if (!email) {
      return 'Email is required.';
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      return 'Enter a valid email address.';
    }
    if (!this.password) {
      return 'Password is required.';
    }
    if (this.password.length < 8 || this.password.length > 128) {
      return 'Password must be between 8 and 128 characters.';
    }
    return null;
  }

  private extractErrorMessage(err: any): string {
    const raw = err?.error;
    if (typeof raw === 'string') {
      try {
        const parsed = JSON.parse(raw);
        return parsed?.message || parsed?.data || raw;
      } catch {
        return raw || 'Authentication failed.';
      }
    }
    return raw?.message || raw?.data || err?.message || 'Authentication failed.';
  }
}
