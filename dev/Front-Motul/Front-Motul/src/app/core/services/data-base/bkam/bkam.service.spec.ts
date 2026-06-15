import { TestBed } from '@angular/core/testing';

import { BkamService } from './bkam.service';

describe('BkamService', () => {
  let service: BkamService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(BkamService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
