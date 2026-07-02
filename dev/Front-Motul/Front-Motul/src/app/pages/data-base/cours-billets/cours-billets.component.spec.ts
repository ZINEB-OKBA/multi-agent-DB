import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CoursBilletsComponent } from './cours-billets.component';

describe('CoursBilletsComponent', () => {
  let component: CoursBilletsComponent;
  let fixture: ComponentFixture<CoursBilletsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CoursBilletsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CoursBilletsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
