import {
  HttpInterceptorFn,
  HttpErrorResponse
} from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, from, switchMap, throwError } from 'rxjs';
import { AuthenticationService } from './authentication.service';
import { SessionStorageService } from './session.storage.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthenticationService);
  const session = inject(SessionStorageService);

  // Define the list of public endpoints
  const excludedUrls = ['/auth/login', '/auth/register'];

  // Check if the request URL matches any of the excluded paths
  const isExcluded = excludedUrls.some(url => req.url.includes(url));

  // If excluded, forward the request without modifying it
  if (isExcluded) {
    return next(req);
  }

  // 🎯 ÉTAPE 1 : On attache TOUJOURS le token JWT, même pour les fichiers/blobs,
  // pour que Spring Boot valide les droits d'accès au téléchargement.
  const accessToken = session.getToken();
  const authReq = accessToken
      ? req.clone({ setHeaders: { Authorization: `Bearer ${accessToken}` } })
      : req;

  return next(authReq).pipe(
      catchError((error: HttpErrorResponse) => {

        // 🎯 ÉTAPE 2 : Si la requête échoue avec un 401 sur un BLOB (téléchargement),
        // on ne tente PAS de rafraîchir le token ici pour éviter de boucler ou de planter sur le port 4200.
        if (req.responseType === 'blob') {
          return throwError(() => error);
        }

        // Logique normale de rafraîchissement pour les autres requêtes JSON standard
        if (error.status === 401) {
          return from(authService.refreshToken()).pipe(
              switchMap((newToken) => {
                if (newToken) {
                  const retryReq = req.clone({
                    setHeaders: { Authorization: `Bearer ${newToken}` }
                  });
                  return next(retryReq);
                } else {
                  authService.logout();
                  return throwError(() => error);
                }
              }),
              catchError(() => {
                authService.logout();
                return throwError(() => error);
              })
          );
        }

        return throwError(() => error);
      })
  );
};