import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchpageComponent } from './searchpage.component';

describe('SearchpageComponent', () => {
  let component: SearchpageComponent;
  let fixture: ComponentFixture<SearchpageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SearchpageComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SearchpageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
