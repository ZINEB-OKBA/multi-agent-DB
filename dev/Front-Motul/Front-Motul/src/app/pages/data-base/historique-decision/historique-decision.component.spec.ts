import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HistoriqueDecisionComponent } from './historique-decision.component';

describe('HistoriqueDecisionComponent', () => {
  let component: HistoriqueDecisionComponent;
  let fixture: ComponentFixture<HistoriqueDecisionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [HistoriqueDecisionComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HistoriqueDecisionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
