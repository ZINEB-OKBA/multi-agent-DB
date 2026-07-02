import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BkamLandingComponent } from './bkam-landing.component';

describe('BkamLandingComponent', () => {
  let component: BkamLandingComponent;
  let fixture: ComponentFixture<BkamLandingComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [BkamLandingComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(BkamLandingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
