import React, { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Message } from '@/types/chat';
import AIAvatar from '@/components/AIAvatar';
import UserAvatar from '@/components/UserAvatar';
import { Maximize2, MessageSquare, Copy, Check, ThumbsUp, ThumbsDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';

type MessageBubbleProps = {
  message: Message;
  isLastMessage?: boolean;
  onAnswerSelect?: (questionMessageId: string, questionText: string, answer: boolean) => void;
};

// Component to render typing indicator animation
const TypingIndicator = () => (
  <div className="typing-indicator">
    <span></span>
    <span></span>
    <span></span>
  </div>
);

// Replace existing formatPlanJsonForDisplay with structured headings and paragraphs:
const formatPlanJsonForDisplay = (planJson: any): React.ReactNode => {
  if (!planJson || typeof planJson !== 'object') return null;
  return (
    <div className="mt-4 space-y-8 text-gray-200">
      {/* Title */}
      {planJson.productName && (
        <h2 className="text-2xl font-bold text-purple-300 mb-4">
          {planJson.productName}
        </h2>
      )}

      {/* Overview */}
      {planJson.summary && (
        <section>
          <h3 className="text-xl font-semibold text-indigo-400">Overview</h3>
          <p className="mt-2 text-gray-300 leading-relaxed">{planJson.summary}</p>
        </section>
      )}

      {/* Target Audience */}
      {planJson.targetAudience && (
        <section>
          <h3 className="text-xl font-semibold text-indigo-400">Target Audience</h3>
          <p className="mt-2 text-gray-300 leading-relaxed">{planJson.targetAudience}</p>
        </section>
      )}

      {/* Core Features */}
      {Array.isArray(planJson.coreFeatures) && (
        <section>
          <h3 className="text-xl font-semibold text-indigo-400">Core Features</h3>
          <ul className="mt-2 list-disc list-inside text-gray-300 space-y-1">
            {planJson.coreFeatures.map((item: string, idx: number) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Key Differentiators */}
      {Array.isArray(planJson.keyDifferentiators) && (
        <section>
          <h3 className="text-xl font-semibold text-indigo-400">Key Differentiators</h3>
          <ul className="mt-2 list-disc list-inside text-gray-300 space-y-1">
            {planJson.keyDifferentiators.map((item: string, idx: number) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Monetization Strategy */}
      {planJson.monetizationStrategy && (
        <section>
          <h3 className="text-xl font-semibold text-indigo-400">Monetization Strategy</h3>
          <p className="mt-2 text-gray-300 leading-relaxed">{planJson.monetizationStrategy}</p>
        </section>
      )}

      {/* Technology Stack */}
      {planJson.technologyStackConsiderations && (
        <section>
          <h3 className="text-xl font-semibold text-indigo-400">Technology Stack</h3>
          <p className="mt-2 text-gray-300 leading-relaxed">{planJson.technologyStackConsiderations}</p>
        </section>
      )}

      {/* Non-functional Requirements */}
      {Array.isArray(planJson.nonFunctionalRequirements) && (
        <section>
          <h3 className="text-xl font-semibold text-indigo-400">Non-functional Requirements</h3>
          <ul className="mt-2 list-disc list-inside text-gray-300 space-y-1">
            {planJson.nonFunctionalRequirements.map((item: string, idx: number) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </section>
      )}

      {/* User Stories */}
      {Array.isArray(planJson.userStories) && (
        <section>
          <h3 className="text-xl font-semibold text-indigo-400">User Stories</h3>
          <ul className="mt-2 list-disc list-inside text-gray-300 space-y-2">
            {planJson.userStories.map((story: any, idx: number) => (
              <li key={idx} className="space-y-1">
                <p><strong>As a</strong> {story.role}</p>
                <p><strong>I want to</strong> {story.action}</p>
                <p><strong>So that</strong> {story.reason}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Future Considerations */}
      {Array.isArray(planJson.futureConsiderations) && (
        <section>
          <h3 className="text-xl font-semibold text-indigo-400">Future Considerations</h3>
          <ul className="mt-2 list-disc list-inside text-gray-300 space-y-1">
            {planJson.futureConsiderations.map((item: string, idx: number) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Additional Fields */}
      {Object.entries(planJson).map(([key, value]) => {
        const skipKeys = ['productName','summary','targetAudience','coreFeatures','keyDifferentiators','monetizationStrategy','technologyStackConsiderations','nonFunctionalRequirements','userStories','futureConsiderations'];
        if (skipKeys.includes(key)) return null;
        return (
          <section key={key}>
            <h3 className="text-xl font-semibold text-indigo-400 capitalize">{key.replace(/([A-Z])/g, ' $1')}</h3>
            <p className="mt-2 font-mono text-gray-300 bg-[#1e1e2e] p-2 rounded">{JSON.stringify(value, null, 2)}</p>
          </section>
        );
      })}
    </div>
  );
};

const MessageBubble = ({ message, isLastMessage = false, onAnswerSelect }: MessageBubbleProps) => {
  const isAI = message.role === 'assistant';
  const [isExpanded, setIsExpanded] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  
  const copyToClipboard = () => {
    if (message.content && navigator.clipboard) {
      navigator.clipboard.writeText(message.content)
        .then(() => {
          setIsCopied(true);
          toast({
            title: "Content copied",
            description: "Message copied to clipboard",
            duration: 2000,
          });
          
          setTimeout(() => setIsCopied(false), 2000);
        })
        .catch(err => {
          console.error('Failed to copy: ', err);
        });
    }
  };
  
  // Reset expanded state when messages change
  useEffect(() => {
    setIsExpanded(false);
  }, [message.id]);
  
  // Calculate if message is long
  const [isLongMessage, setIsLongMessage] = useState(false);
  
  useEffect(() => {
    if (contentRef.current && !message.isLoading) {
      setIsLongMessage(contentRef.current.scrollHeight > 300);
    }
  }, [message.content, message.isLoading]);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }} // Simpler initial state: fade in and slight slide up
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        type: "tween", // Changed from spring to tween for less bounciness
        ease: "easeOut", // Common easing function
        duration: 0.3, // Faster duration
        delay: isLastMessage ? 0 : 0 
      }}
      className={cn(
        'flex gap-5 py-6 relative',
        isAI ? 'items-start' : 'items-start justify-end',
        'relative z-10'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Message timestamp indicator line */}
      <div className="absolute top-0 left-0 right-0 flex items-center justify-center">
        <div className="px-3 py-1 text-xs text-muted-foreground/70 bg-background/40 backdrop-blur-md rounded-full">
          {new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
        </div>
      </div>

      {isAI && (
        <div 
          className={cn(
            "flex-shrink-0 pt-1",
            "transform transition-all duration-500",
            isHovered ? "scale-110" : "scale-100",
            "hover:animate-pulse-ring"
          )}
        >
          <div className="relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full blur opacity-70 group-hover:opacity-90 animate-gradient-shift"></div>
            <div className="relative">
              <AIAvatar emotion={message.emotion || 'neutral'} />
            </div>
          </div>
        </div>
      )}

      <div className={cn(
        "relative max-w-[85%] group",
        isAI ? "w-full" : ""
      )}>
        <motion.div
          className={cn(
            "p-5 rounded-2xl max-w-full shadow-xl relative overflow-hidden",
            isAI
              ? "rounded-tl-sm bg-gradient-to-br from-[#1a1f3b]/90 via-[#252a4b]/90 to-[#1e1b4b]/90 text-white backdrop-blur-md border border-white/10"
              : "rounded-tr-sm bg-gradient-to-r from-[#7c3aed] via-[#8b5cf6] to-[#6d28d9] text-white",
            isHovered && "shadow-2xl ring-1 ring-white/20",
          )}
          whileHover={{ scale: 1.01 }}
          transition={{ type: "spring", stiffness: 400, damping: 10 }}
          layout
        >
          {/* Animated glow effect in background */}
          <div className="absolute inset-0 overflow-hidden">
            <div className={cn(
              "absolute inset-0 opacity-30",
              isAI ? "bg-nebula-glow" : "bg-user-glow"
            )}></div>
          </div>
          
          {/* Message content */}
          {message.isLoading ? (
            <div className="flex items-center justify-center py-4">
              <div className="futuristic-loader">
                <div></div>
                <div></div>
                <div></div>
                <div></div>
              </div>
            </div>
          ) : (
            <div className="relative">
              <div 
                ref={contentRef}
                className={cn(
                  "relative overflow-hidden transition-all",
                  isExpanded ? "max-h-none" : "max-h-[300px]"
                )}
              >
                {/* Render text content */}
                <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-[#1a1a2e] prose-pre:border prose-pre:border-white/10">
                  {message.content}
                </div>

                {/* Conditionally render Yes/No buttons for questions */}
                {isAI && message.isQuestion && onAnswerSelect && !message.answered && ( // Added !message.answered
                  <div className="mt-4 flex space-x-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="bg-green-500 hover:bg-green-600 text-white"
                      onClick={() => onAnswerSelect(message.id, message.content, true)}
                    >
                      Yes
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="bg-red-500 hover:bg-red-600 text-white"
                      onClick={() => onAnswerSelect(message.id, message.content, false)}
                    >
                      No
                    </Button>
                  </div>
                )}

                {/* Display formatted JSON plan if available */}
                {message.planJson && typeof message.planJson === 'object' && Object.keys(message.planJson).length > 0 && (
                  <div className="mt-4 rounded-md">
                    {formatPlanJsonForDisplay(message.planJson)}
                  </div>
                )}
                
                {/* Render any images */}
                {message.images && message.images.length > 0 && (
                  <div className="mt-4 grid grid-cols-2 gap-3">
                    {message.images.map((img, i) => (
                      <motion.div 
                        key={i}
                        whileHover={{ 
                          scale: 1.05, 
                          y: -5,
                          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.2)"
                        }}
                        className="relative rounded-lg overflow-hidden group/image"
                      >
                        <img
                          src={img}
                          alt={`Image ${i + 1}`}
                          className="rounded-lg max-h-64 w-full object-cover hover:z-10"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover/image:opacity-100 transition-opacity flex items-end justify-center p-3">
                          <button className="text-xs text-white px-2 py-1 bg-black/30 backdrop-blur-sm rounded-full">
                            View full
                          </button>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
                
                {/* Gradient fade effect for long messages */}
                {!isExpanded && isLongMessage && (
                  <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-[#1a1f3b]/90 to-transparent pointer-events-none"></div>
                )}
              </div>
            </div>
          )}
          
          {/* Dynamic particle effect in background */}
          <div className="particles absolute inset-0 overflow-hidden pointer-events-none"></div>
        </motion.div>
        
        {/* Message actions */}
        <AnimatePresence>
          {isHovered && !message.isLoading && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className={cn(
                "absolute -bottom-4 flex items-center gap-1 bg-muted/30 backdrop-blur-md p-1 rounded-full border border-white/10 shadow-xl",
                isAI ? "left-4" : "right-4"
              )}
            >
              <button 
                onClick={copyToClipboard} 
                className="p-1.5 rounded-full hover:bg-white/10 transition-colors"
                title="Copy to clipboard"
              >
                {isCopied ? <Check size={12} /> : <Copy size={12} />}
              </button>
              
              {isLongMessage && (
                <button 
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="p-1.5 rounded-full hover:bg-white/10 transition-colors"
                  title={isExpanded ? "Show less" : "Show more"}
                >
                  <Maximize2 size={12} />
                </button>
              )}
              
              {isAI && (
                <>
                  <div className="w-px h-3 bg-white/10"></div>
                  <button 
                    className="p-1.5 rounded-full hover:bg-white/10 transition-colors" 
                    title="Helpful"
                  >
                    <ThumbsUp size={12} />
                  </button>
                  <button 
                    className="p-1.5 rounded-full hover:bg-white/10 transition-colors"
                    title="Not helpful"
                  >
                    <ThumbsDown size={12} />
                  </button>
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {!isAI && (
        <div className="flex-shrink-0 pt-1">
          <div className="relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-violet-600 via-indigo-600 to-blue-700 rounded-full blur opacity-70 group-hover:opacity-90 animate-gradient-shift"></div>
            <div className="relative">
              <UserAvatar />
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default MessageBubble;
