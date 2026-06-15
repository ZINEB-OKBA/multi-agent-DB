import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UtilisateurProfilComponent } from './utilisateur-profil.component';

describe('UtilisateurProfilComponent', () => {
  let component: UtilisateurProfilComponent;
  let fixture: ComponentFixture<UtilisateurProfilComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [UtilisateurProfilComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(UtilisateurProfilComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
