import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ActionBtn } from './action-btn';

describe('ActionBtn', () => {
  let component: ActionBtn;
  let fixture: ComponentFixture<ActionBtn>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ActionBtn]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ActionBtn);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
