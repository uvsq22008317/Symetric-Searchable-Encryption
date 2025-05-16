import { Component, inject, NgModule } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import {MatButtonModule} from '@angular/material/button';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {  MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import {MatListModule} from '@angular/material/list';
import { MatTableModule } from '@angular/material/table';
import { CommonModule } from '@angular/common';
import { MatDialog } from '@angular/material/dialog';
import { DocumentDialogComponent } from '../document-dialog/document-dialog.component';
import { HttpClient } from '@angular/common/http';
import { FormControl, FormGroup, FormsModule } from '@angular/forms';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { catchError, throwError } from 'rxjs';


@Component({
  standalone: true,
  selector: 'app-searchpage',
  imports: [CommonModule,RouterOutlet,MatFormFieldModule,CommonModule, MatTableModule,MatInputModule,
    MatListModule, MatButtonModule, MatIconModule,MatPaginatorModule,MatProgressSpinnerModule,FormsModule],
    
    templateUrl: './searchpage.component.html',
    styleUrl: './searchpage.component.css'
  })
export class SearchpageComponent{
private http = inject(HttpClient);
private url = //'http://localhost:8000/search';
'https://dsseserverter.zapto.org:443/search';
title = 'front-ter';
currentPage = 0;
totalItems = 0;
pageSize = 5;
word = ''
isLoading = true;
isNotFound = false;
message = ''
display = false;
dialog = inject(MatDialog);
allItems: { name: string,content:string,showText:boolean }[] = [] 

items = this.getData(this.currentPage, this.pageSize);

public pageChanged(event: PageEvent) {
  this.currentPage = event.pageIndex;
  this.pageSize = event.pageSize;
  this.items = this.getData(this.currentPage, this.pageSize);
}

public getData(page: number,pageSize: number){
const startIndex = page*pageSize;
return this.allItems.slice(startIndex,startIndex+pageSize);
}

afficherDocument(text :String){
 
  let dialogRef = this.dialog.open(DocumentDialogComponent, {
    height: '90vh',
    width: '90vw',
    
    data: {text: text},
  });
}

search(){
  this.isLoading = true;
  
    this.http.post(this.url,{"word" :this.word})
    .pipe(
      catchError((_) => {
        this.isNotFound = true;
        this.message = "Probleme de connection au serveur";
        return throwError(()=> new Error('Probleme de connection au serveur'))
      })
      )
    .subscribe((data: any) => {
    
     console.log(data)
     this.allItems = data.result;
     this.items = this.getData(this.currentPage, this.pageSize); 
     this.isLoading = false;
    if (this.items.length == 0){
      this.isNotFound = true;
      this.message = "Aucun document trouvé"
    }else{
      this.isNotFound = false;
      this.display = true;
      this.totalItems = this.allItems.length;
    }
     
     
     


    })
   
}



 
}





