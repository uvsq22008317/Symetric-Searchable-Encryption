import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogActions, MatDialogContent, MatDialogModule, MatDialogRef, MatDialogTitle } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-document-dialog',
  imports: [MatButtonModule,MatIconModule, CommonModule,
    MatButtonModule,
    MatDialogActions,
    MatDialogModule,
    MatDialogContent,
    MatDialogTitle],
  templateUrl: './document-dialog.component.html',
  styleUrl: './document-dialog.component.css'
})
export class DocumentDialogComponent {
  data = inject(MAT_DIALOG_DATA);
  dialogRef = inject(MatDialogRef<DocumentDialogComponent>);

  onClick(): void {
    this.dialogRef.close();
  }
}
