import { TestBed } from '@angular/core/testing';

import { AmmcService } from './ammc.service';

describe('AmmcService', () => {
  let service: AmmcService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AmmcService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
