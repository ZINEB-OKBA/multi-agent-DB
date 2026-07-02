import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HistoriqueAccesListComponent } from './historique-acces-list.component';

describe('HistoriqueAccesListComponent', () => {
  let component: HistoriqueAccesListComponent;
  let fixture: ComponentFixture<HistoriqueAccesListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [HistoriqueAccesListComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HistoriqueAccesListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
