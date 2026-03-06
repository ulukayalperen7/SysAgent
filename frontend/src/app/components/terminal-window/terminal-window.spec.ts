import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TerminalWindow } from './terminal-window';

describe('TerminalWindow', () => {
  let component: TerminalWindow;
  let fixture: ComponentFixture<TerminalWindow>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TerminalWindow]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TerminalWindow);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
