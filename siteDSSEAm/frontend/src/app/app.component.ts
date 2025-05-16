import { Component, Inject, inject, NgModule } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import {MatButtonModule} from '@angular/material/button';
import { CommonModule, DOCUMENT } from '@angular/common';

import { AuthService } from '@auth0/auth0-angular';
@Component({
  selector: 'app-root',
  imports: [CommonModule,RouterOutlet,MatButtonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent{

constructor(public auth: AuthService , @Inject(DOCUMENT) public document: Document) {}



  logout() {
    this.auth.logout({ 
      logoutParams: {
        returnTo: this.document.location.origin 
      }
    });
  }
 
}





