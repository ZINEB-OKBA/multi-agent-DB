import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MarcheMonetaireComponent } from './marche-monetaire.component';

describe('MarcheMonetaireComponent', () => {
  let component: MarcheMonetaireComponent;
  let fixture: ComponentFixture<MarcheMonetaireComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MarcheMonetaireComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MarcheMonetaireComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
