import { TestBed } from '@angular/core/testing';

import { AsfimService } from './asfim.service';

describe('AsfimService', () => {
  let service: AsfimService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AsfimService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
