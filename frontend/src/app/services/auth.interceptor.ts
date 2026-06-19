import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
    const auth = inject(AuthService);
    const token = auth.token;
    const authedReq = token
        ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
        : req;

    return next(authedReq).pipe(
        catchError(error => {
            if (error?.status === 401 && !req.url.includes('/auth/login') && !req.url.includes('/auth/register')) {
                auth.logout();
            }
            return throwError(() => error);
        })
    );
};
