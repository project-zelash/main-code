
import React from 'react';
import { Check, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export type AIPersona = {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
};

type PersonaSelectorProps = {
  personas: AIPersona[];
  selectedPersona: AIPersona;
  onSelect: (persona: AIPersona) => void;
  className?: string;
};

const PersonaSelector = ({
  personas,
  selectedPersona,
  onSelect,
  className,
}: PersonaSelectorProps) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-md transition-all',
          'text-sm font-medium hover:bg-white/10',
          'border border-white/10 bg-white/5',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500',
          className
        )}
      >
        <span className={cn('w-2 h-2 rounded-full', selectedPersona.color)} />
        <span>{selectedPersona.name}</span>
        <ChevronDown className="h-4 w-4 text-muted-foreground" />
      </DropdownMenuTrigger>
      
      <DropdownMenuContent
        align="end"
        className="w-56 overflow-hidden p-0 ai-glass border-white/10"
      >
        <div className="p-1.5">
          {personas.map((persona) => (
            <DropdownMenuItem
              key={persona.id}
              className={cn(
                'flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer',
                'focus:bg-white/10 hover:bg-white/10',
                selectedPersona.id === persona.id && 'bg-white/5'
              )}
              onClick={() => onSelect(persona)}
            >
              <div className="flex items-center gap-2 flex-1">
                <span className={cn('w-2 h-2 rounded-full', persona.color)} />
                <span>{persona.name}</span>
              </div>
              {selectedPersona.id === persona.id && (
                <Check className="h-4 w-4 text-violet-500" />
              )}
            </DropdownMenuItem>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default PersonaSelector;
