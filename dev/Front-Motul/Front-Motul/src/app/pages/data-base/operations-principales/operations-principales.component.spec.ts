import { ComponentFixture, TestBed } from '@angular/core/testing';

import { OperationsPrincipalesComponent } from './operations-principales.component';

describe('OperationsPrincipalesComponent', () => {
  let component: OperationsPrincipalesComponent;
  let fixture: ComponentFixture<OperationsPrincipalesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [OperationsPrincipalesComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(OperationsPrincipalesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
