import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';
import { provideAuth0 } from '@auth0/auth0-angular';
import { provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { routes } from './app/app.routes';
bootstrapApplication(AppComponent,  {
  providers: [
    provideAuth0({
      domain: 'dev-w4t2fy25wc73e8qe.eu.auth0.com',
      clientId: 'bzKpmJlxxFwSeYLQrwk18pgQ2kNVNqrX',
      authorizationParams: {
        redirect_uri: window.location.origin
      }
    }),
    provideZoneChangeDetection({ eventCoalescing: true }),
     provideRouter(routes),
    provideHttpClient( withFetch(),)
  ]
},)
  .catch((err) => console.error(err));
