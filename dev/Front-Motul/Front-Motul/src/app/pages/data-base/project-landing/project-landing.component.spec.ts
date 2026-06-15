import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectLandingComponent } from './project-landing.component';

describe('ProjectListComponent', () => {
  let component: ProjectLandingComponent;
  let fixture: ComponentFixture<ProjectLandingComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ProjectLandingComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProjectLandingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
