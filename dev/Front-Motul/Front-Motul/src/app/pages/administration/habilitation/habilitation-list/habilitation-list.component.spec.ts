import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HabilitationListComponent } from './habilitation-list.component';

describe('HabilitationListComponent', () => {
  let component: HabilitationListComponent;
  let fixture: ComponentFixture<HabilitationListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [HabilitationListComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HabilitationListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
