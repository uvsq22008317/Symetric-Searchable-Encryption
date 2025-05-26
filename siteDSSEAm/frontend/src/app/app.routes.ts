import { Routes } from '@angular/router';
import { SearchpageComponent } from './searchpage/searchpage.component';
import { UpdateComponent } from './update/update.component';
import { AuthGuard } from '@auth0/auth0-angular';
export const routes: Routes = [
{path: 'search', component: SearchpageComponent,canActivate: [AuthGuard]},
{ path: 'upload', component: UpdateComponent }
];
