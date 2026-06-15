import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BandeFluctuationComponent } from './bande-fluctuation.component';

describe('BandeFluctuationComponent', () => {
  let component: BandeFluctuationComponent;
  let fixture: ComponentFixture<BandeFluctuationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [BandeFluctuationComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(BandeFluctuationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
