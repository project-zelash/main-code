
import React, { useState, useRef, useEffect } from 'react';
import { Mic, Send, Image, Paperclip, X, Smile, Command, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { motion, AnimatePresence } from 'framer-motion';

type ChatInputProps = {
  onSendMessage: (message: string, attachments?: File[]) => void;
  className?: string;
  isAIThinking?: boolean;
};

const ChatInput = ({ onSendMessage, className, isAIThinking = false }: ChatInputProps) => {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [isComposing, setIsComposing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const composingTimeoutRef = useRef<NodeJS.Timeout>();
  
  const handleSend = () => {
    if (message.trim() || attachments.length > 0) {
      onSendMessage(message, attachments);
      setMessage('');
      setAttachments([]);
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleKeyDown = () => {
    setIsComposing(true);
    
    // Clear existing timeout
    if (composingTimeoutRef.current) {
      clearTimeout(composingTimeoutRef.current);
    }
    
    // Set new timeout
    composingTimeoutRef.current = setTimeout(() => {
      setIsComposing(false);
    }, 1000);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setAttachments(prev => [...prev, ...newFiles]);
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments(attachments.filter((_, i) => i !== index));
  };
  
  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [message]);
  
  // Focus textarea on mount
  useEffect(() => {
    if (!isAIThinking && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isAIThinking]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (composingTimeoutRef.current) {
        clearTimeout(composingTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className={cn('relative', className)}>
      {/* Attachments preview */}
      <AnimatePresence>
        {attachments.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="flex flex-wrap gap-2 mb-3 p-3 rounded-lg backdrop-blur-lg bg-muted/10 border border-white/10 shadow-lg"
          >
            {attachments.map((file, index) => (
              <motion.div 
                key={index} 
                className="relative group transform-3d-hover"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              >
                <div className="flex items-center gap-2 px-3 py-2 bg-muted/20 backdrop-blur-md rounded-lg border border-white/10 shadow-lg">
                  <Paperclip className="h-3 w-3 text-indigo-300" />
                  <span className="max-w-[150px] truncate text-sm">{file.name}</span>
                  <button 
                    className="text-muted-foreground hover:text-foreground hover:bg-white/10 rounded-full p-1 transition-colors"
                    onClick={() => removeAttachment(index)}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Input area */}
      <div className="relative">
        {/* Advanced gradient outline effect */}
        <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-1000 group-hover:duration-200 animate-gradient-shift"></div>
        
        <div className="relative flex items-end gap-2 rounded-2xl px-4 py-3 bg-[#1a1f3b]/70 backdrop-blur-xl focus-within:ring-1 focus-within:ring-violet-500/50 border border-white/10 shadow-[0_8px_30px_rgb(0,0,0,0.12)]">
          <div className="flex-1 min-w-0">
            <textarea
              ref={textareaRef}
              placeholder={isAIThinking ? "AI is thinking..." : "Type your message..."}
              className={cn(
                "w-full resize-none bg-transparent outline-none min-h-[44px] max-h-[200px] py-2 px-1 placeholder:text-muted-foreground/70 text-base",
                isAIThinking && "opacity-50"
              )}
              rows={1}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              onKeyPress={handleKeyPress}
              disabled={isAIThinking}
              style={{
                overflowY: 'auto',
              }}
            />
          </div>
          
          <div className="flex items-center gap-1.5 pb-2">
            {/* Image upload */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              multiple
              accept="image/*"
            />
            
            <div className="flex space-x-1">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className={cn(
                      "h-9 w-9 rounded-full text-muted-foreground hover:bg-violet-500/20 hover:text-violet-400 transition-all duration-200",
                      isAIThinking && "opacity-50 pointer-events-none"
                    )}
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isAIThinking}
                  >
                    <Image className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Attach image</TooltipContent>
              </Tooltip>
              
              {/* Voice input */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className={cn(
                      "h-9 w-9 rounded-full text-muted-foreground hover:bg-violet-500/20 hover:text-violet-400 transition-all duration-200",
                      isAIThinking && "opacity-50 pointer-events-none"
                    )}
                    disabled={isAIThinking}
                  >
                    <Mic className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Voice input</TooltipContent>
              </Tooltip>
              
              {/* Emoji picker */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className={cn(
                      "h-9 w-9 rounded-full text-muted-foreground hover:bg-violet-500/20 hover:text-violet-400 transition-all duration-200",
                      isAIThinking && "opacity-50 pointer-events-none"
                    )}
                    disabled={isAIThinking}
                  >
                    <Smile className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Add emoji</TooltipContent>
              </Tooltip>
              
              {/* Command palette */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className={cn(
                      "h-9 w-9 rounded-full text-muted-foreground hover:bg-violet-500/20 hover:text-violet-400 transition-all duration-200",
                      isAIThinking && "opacity-50 pointer-events-none"
                    )}
                    disabled={isAIThinking}
                  >
                    <Command className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Commands</TooltipContent>
              </Tooltip>
            </div>
            
            {/* Send button */}
            <div className="relative h-10 w-10 ml-1">
              <AnimatePresence mode="wait">
                {(message.trim() || attachments.length > 0) ? (
                  <motion.div 
                    key="send-active"
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.8, opacity: 0 }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    className="absolute inset-0"
                  >
                    <Button
                      variant="ghost"
                      size="icon"
                      className={cn(
                        "h-10 w-10 rounded-full transition-all duration-300 shadow-lg relative",
                        "bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 text-white",
                        "hover:shadow-[0_0_20px_rgba(139,92,246,0.5)]",
                        isAIThinking && "opacity-50 pointer-events-none"
                      )}
                      onClick={handleSend}
                      disabled={isAIThinking || (!message.trim() && attachments.length === 0)}
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-700 rounded-full blur opacity-40 group-hover:opacity-60 transition duration-1000 group-hover:duration-200 animate-pulse-slow"></div>
                      <Send className="h-4 w-4 z-10 relative" />
                    </Button>
                  </motion.div>
                ) : (
                  <motion.div 
                    key="send-inactive"
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.8, opacity: 0 }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    className="absolute inset-0"
                  >
                    <Button
                      variant="ghost"
                      size="icon"
                      className={cn(
                        "h-10 w-10 rounded-full relative",
                        "bg-muted/30 text-muted-foreground",
                        isAIThinking && "opacity-50 pointer-events-none"
                      )}
                      disabled={true}
                    >
                      <Sparkles className="h-4 w-4" />
                    </Button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
      
      {/* Composition indicator */}
      <div className="mt-2 text-xs text-center">
        <AnimatePresence>
          {isComposing && !isAIThinking && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-muted-foreground text-xs"
            >
              Composing message...
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ChatInput;
