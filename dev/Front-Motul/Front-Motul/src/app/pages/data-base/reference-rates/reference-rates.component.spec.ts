import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ReferenceRatesComponent } from './reference-rates.component';

describe('ReferenceRatesComponent', () => {
  let component: ReferenceRatesComponent;
  let fixture: ComponentFixture<ReferenceRatesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ReferenceRatesComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ReferenceRatesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
