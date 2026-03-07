import { ApplicationConfig, provideBrowserGlobalErrorListeners, importProvidersFrom } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { LucideAngularModule, TerminalSquare, Cpu, PackageSearch, Workflow, History, Search, Monitor, Laptop, Server, Copy, FolderSearch, Blocks, ScanSearch, ShieldCheck, Download, FolderOpen, Clock, Zap } from 'lucide-angular';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withFetch()),
    importProvidersFrom(
      LucideAngularModule.pick({
        TerminalSquare,
        Cpu,
        PackageSearch,
        Workflow,
        History,
        Search,
        Monitor,
        Laptop,
        Server,
        Copy,
        FolderSearch,
        Blocks,
        ScanSearch,
        ShieldCheck,
        Download,
        FolderOpen,
        Clock,
        Zap
      })
    )
  ]
};
