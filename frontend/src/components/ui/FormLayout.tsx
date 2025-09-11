import { ReactNode } from 'react';

interface FormLayoutProps {
  children: ReactNode; // This will be the FormGrid
  actions: ReactNode;  // This will be the Buttons
  className?: string;
}

export function FormLayout({ children, actions, className }: FormLayoutProps) {
  return (
    <div className={`flex flex-col gap-4 mb-6 ${className || ''}`}>
      <div>{children}</div>
      <div className="flex justify-start gap-2">
        {actions}
      </div>
    </div>
  );
}
