// src/app/layout.tsx
import "../styles/globals.css";

import type { ReactNode } from 'react';

export default function RootLayout({ children }: { children: ReactNode }) {
    return (
        <html lang="vi">
            <body>{children}</body>
        </html>
    );
}
