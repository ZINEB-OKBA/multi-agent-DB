import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AmmcComponent } from './ammc.component';

describe('AmmcComponent', () => {
  let component: AmmcComponent;
  let fixture: ComponentFixture<AmmcComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AmmcComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AmmcComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
