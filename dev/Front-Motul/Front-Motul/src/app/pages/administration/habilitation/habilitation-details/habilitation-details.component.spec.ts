import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HabilitationDetailsComponent } from './habilitation-details.component';

describe('HabilitationDetailsComponent', () => {
  let component: HabilitationDetailsComponent;
  let fixture: ComponentFixture<HabilitationDetailsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [HabilitationDetailsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HabilitationDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
