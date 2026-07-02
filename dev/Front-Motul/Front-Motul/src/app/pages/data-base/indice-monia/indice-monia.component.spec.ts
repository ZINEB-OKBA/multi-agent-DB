import { ComponentFixture, TestBed } from '@angular/core/testing';

import { IndiceMoniaComponent } from './indice-monia.component';

describe('IndiceMoniaComponent', () => {
  let component: IndiceMoniaComponent;
  let fixture: ComponentFixture<IndiceMoniaComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [IndiceMoniaComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(IndiceMoniaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
