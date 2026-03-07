import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import {
  LucideAngularModule,
  TerminalSquare,
  Cpu,
  PackageSearch,
  Workflow,
  History
} from 'lucide-angular';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    LucideAngularModule
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  // Root shell for SysAgent
}
