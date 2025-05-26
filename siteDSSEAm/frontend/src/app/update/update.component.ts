import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatOptionModule } from '@angular/material/core';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { RouterModule } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-update',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatSelectModule,
    MatOptionModule,
    MatInputModule,
    MatButtonModule,
    RouterModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './update.component.html',
  styleUrls: ['./update.component.css']
})

export class UpdateComponent implements OnInit {
  private apiUrl = 'https://dsseserverter.zapto.org:443/update';
  documents: string[] = [];
  selectedDocument: string | null = null;
  documentContent: string = '';
  isLoading = true;
  errorMessage = '';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadDocuments();
  }

  loadDocuments(): void {
    this.isLoading = true;
    this.http.get<{ documents: string[] }>(this.apiUrl)
      .pipe(
        catchError(err => {
          this.errorMessage = 'Erreur de connexion au serveur';
          this.isLoading = false;
          return throwError(() => new Error(err));
        })
      )
      .subscribe({
        next: (response: any) => {
          console.log('Réponse API:', response);
          this.documents = response.documents || [];
          this.isLoading = false;
          if (this.documents.length === 0) {
            this.errorMessage = 'Aucun document disponible';
          }
        },
        error: (err) => {
          console.error('Erreur:', err);
          this.isLoading = false;
          this.errorMessage = 'Erreur lors du chargement des documents';
        }
      });
  }

  loadDocumentContent(): void {
    if (this.selectedDocument) {
      this.http.get<{ content: string }>(`/api/documents/${this.selectedDocument}`)
        .subscribe({
          next: (response) => this.documentContent = response.content,
          error: (err) => console.error('Erreur lors du chargement du document :', err)
        });
    }
  }

  updateDocument(): void {
    if (this.selectedDocument && this.documentContent.trim() !== '') {
      this.http.put(`/api/documents/${this.selectedDocument}`, { content: this.documentContent })
        .subscribe({
          next: () => alert('Document mis à jour avec succès !'),
          error: (err) => console.error('Erreur lors de la mise à jour du document :', err)
        });
    } else {
      alert('Veuillez sélectionner un document et saisir du contenu.');
    }
  }
}