import { TestBed } from '@angular/core/testing';

import { AsfimDataService } from './asfim-data.service';

describe('AsfimDataService', () => {
  let service: AsfimDataService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AsfimDataService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
