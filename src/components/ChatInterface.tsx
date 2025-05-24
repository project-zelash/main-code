import React, { useState, useEffect, useRef, Dispatch, SetStateAction } from 'react';
import { cn } from '@/lib/utils';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Settings, Info, History, Brain, Sparkles, X, Menu, Zap, Wand2, ChevronLeft, ChevronRight, Lightbulb } from 'lucide-react';
import ChatInput from '@/components/ChatInput';
import MessageBubble from '@/components/MessageBubble';
import AIAvatar from '@/components/AIAvatar';
import PersonaSelector from '@/components/PersonaSelector';
import { type AIPersona as PersonaSelectorAIPersona } from '@/components/PersonaSelector';
import { generateContentWithGemini } from '../lib/gemini';
import { Message } from '../types/chat';
import { AIPersona } from '@/types/persona'; // Main persona type - CORRECTED PATH
import { Button } from '@/components/ui/button';
import { Drawer, DrawerTrigger, DrawerContent } from '@/components/ui/drawer';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip';
import { Dialog, DialogTrigger, DialogContent } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { useIsMobile } from '@/hooks/use-mobile';

interface ChatInterfaceProps {
  // persona prop might be deprecated if we set a default Product Strategist
}

// Define the primary persona for the project
const productStrategistPersona: AIPersona = {
  id: 'product-strategist',
  name: 'Product Strategist',
  description: 'Helps you refine product ideas into actionable plans.',
  icon: <Lightbulb size={16} />,
  color: 'bg-blue-500',
  avatarUrl: '/placeholder.svg', // Replace with a fitting avatar
  systemInstruction: `You are the world’s most insightful and capable product planner. Your expertise lies in transforming abstract or imaginative product ideas—whether for a web app, mobile app, or a full end-to-end system—into clear, actionable, and innovative product plans.

**Critical Interaction Protocol: STRICTLY FOLLOW THIS**
1.  **User's Initial Idea:** Wait for the user to describe their product idea. Do not ask any questions until they provide this. Your first response after they provide their idea should be your *first single yes/no question*.
2.  **One Question at a Time:** After their initial description, you will ask **ONLY ONE** strategic yes/no question at a time. Your entire response should be *just the question* and do not move on to the next question until a yes or no is received from the user, if any other response is recieved revert back to the same question in a rephrased way. This is crucial to ensure clarity and focus in the conversation.
3.  **Wait for User's Reply:** After asking a question, wait for the user's response.
4.  **Contextual Next Question:** Based on their answer, formulate and ask the **NEXT SINGLE** yes/no question. Again, your response should be *only the question*.
5.  **Question Limit:** Repeat this process for a maximum of 10 questions.
6.  **No Assumptions/Filler:** Every question must be directly aligned with building the exact product the user envisions. Make no assumptions. Do not use conversational filler before or after your question.
7.  **Plan Generation:** Once you believe you have sufficient information (after several questions, up to the 20-question limit), or if the user indicates they have no more details to add, synthesize the gathered information into a coherent product plan. Present this plan to the user in a clear, readable format.
8.  **JSON Output:** After presenting the plan, your **VERY NEXT and FINAL response** should be the complete product plan formatted as a JSON object. Do not add any conversational text before or after the JSON block. The JSON should be structured logically, for example:
    {
      "productName": "User's Product Idea (if specified, or a placeholder)",
      "targetAudience": "...",
      "coreFeatures": ["...", "...", "..."],
      "keyDifferentiators": ["...", "..."],
      "monetizationStrategy": "(if discussed, or 'To be determined')",
      "technologyStackConsiderations": "(if discussed, or 'To be determined')",
      "summary": "A brief overview of the refined product concept."
    }
    Ensure the JSON is valid.

Your primary goal is to help the user clarify their vision and develop an actionable product plan.`,
};

// Other personas can be added here if needed, or this can be the sole persona
const availablePersonas: AIPersona[] = [
  productStrategistPersona,
  // Example of another persona:
  // {
  //   id: \"general-assistant\",
  //   name: \"General Assistant\",
  //   description: \"Your friendly general-purpose AI helper.\",
  //   icon: <Sparkles size={16} />,
  //   color: \"bg-violet-500\",
  //   avatarUrl: \"/placeholder.svg\",
  //   systemInstruction: \"You are a helpful general assistant. Be friendly and concise.\"
  // }
];

const initialMessages: Message[] = [
  {
    id: '1',
    content: `Welcome! Tell me about your product idea, and I'll help you build your vision!`,
    role: 'assistant',
    timestamp: new Date().toISOString(),
    emotion: 'happy'
  }
];

// Helper to map main AIPersona to PersonaSelectorAIPersona
const toSelectorPersona = (persona: AIPersona): PersonaSelectorAIPersona => ({
  id: persona.id,
  name: persona.name,
  description: persona.description,
  icon: persona.icon,
  color: persona.color || 'bg-gray-500', // Fallback color
});

const ChatInterface: React.FC<ChatInterfaceProps> = (/*{ persona: initialPersona }*/) => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isAIThinking, setIsAIThinking] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState<AIPersona>(productStrategistPersona);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  const isMobile = useIsMobile();
  const [isAwaitingYesNo, setIsAwaitingYesNo] = useState<boolean>(false);
  const [currentBotQuestion, setCurrentBotQuestion] = useState<string | null>(null);

  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
    } else {
      setSidebarOpen(true);
    }
  }, [isMobile]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (messageContent: string) => { 
    if (messageContent.trim()) {
      setIsAIThinking(true);
      const userMessage: Message = {
        id: Date.now().toString(),
        content: messageContent, 
        role: 'user',
        timestamp: new Date().toISOString(),
      };
      setMessages((prevMessages) => [...prevMessages, userMessage]);

      let promptToSend = messageContent;
      if (isAwaitingYesNo && currentBotQuestion) {
        promptToSend = `Previous question: "${currentBotQuestion}"\nUser answer: "${messageContent}"\nNow ask the next single yes/no question based on this, or if you have enough information, provide a plan summary.`;
        setIsAwaitingYesNo(false); // Reset after user answers
        setCurrentBotQuestion(null);
      }

      try {
        const systemInstruction = selectedPersona.systemInstruction || "You are a helpful assistant.";
        const botResponseText = await generateContentWithGemini(promptToSend, systemInstruction);
        
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: botResponseText,
          role: 'assistant',
          timestamp: new Date().toISOString(),
          emotion: 'neutral',
        };
        setMessages((prevMessages) => [...prevMessages, botMessage]);

        // Check if the bot's response is a question (simple check, can be improved)
        if (botResponseText.trim().endsWith('?')) {
          setIsAwaitingYesNo(true);
          setCurrentBotQuestion(botResponseText);
        } else {
          setIsAwaitingYesNo(false); // If it's not a question, reset
          setCurrentBotQuestion(null);
        }

      } catch (error: any) {
        console.error("Failed to get response from Gemini:", error);
        const errorMessageContent = error.message && error.message.startsWith('API Error') 
            ? error.message 
            : "Sorry, I'm having trouble connecting. Please try again later.";
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: errorMessageContent,
          role: 'assistant',
          timestamp: new Date().toISOString(),
          emotion: 'concerned',
        };
        setMessages((prevMessages) => [...prevMessages, errorMessage]);
        setIsAwaitingYesNo(false); // Reset on error
        setCurrentBotQuestion(null);
      }
      setIsAIThinking(false);
    }
  };

  const handleClearChat = () => {
    setMessages(initialMessages); // Reset with Product Strategist welcome
    toast({
      title: "Fresh start!",
      description: `Ready to strategize with the ${selectedPersona.name}.`,
      duration: 3000
    });
  };

  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev);
  };

  const SidebarContent = () => (
    <Tabs defaultValue="info" className="h-full flex flex-col">
      <TabsList className="w-full justify-start border-b border-gray-600/30 rounded-none bg-transparent px-2 py-2">
        <TabsTrigger value="info" className="data-[state=active]:bg-gray-600/20 data-[state=active]:text-foreground">
          <Info className="h-4 w-4" />
        </TabsTrigger>
        <TabsTrigger value="memory" className="data-[state=active]:bg-gray-600/20 data-[state=active]:text-foreground">
          <Brain className="h-4 w-4" />
        </TabsTrigger>
        <TabsTrigger value="history" className="data-[state=active]:bg-gray-600/20 data-[state=active]:text-foreground">
          <History className="h-4 w-4" />
        </TabsTrigger>
        <TabsTrigger value="settings" className="data-[state=active]:bg-gray-600/20 data-[state=active]:text-foreground">
          <Settings className="h-4 w-4" />
        </TabsTrigger>
      </TabsList>
      
      <div className="flex-1 overflow-y-auto">
        <TabsContent value="info" className="m-0 p-4 h-full">
          <h3 className="font-medium mb-2">Your AI Assistant</h3>
          <div className="p-3 rounded-lg bg-gray-600/10 mb-4 ai-hover-lift">
            <div className="flex items-center gap-2 mb-1">
              {selectedPersona.icon && <span className="mr-1">{selectedPersona.icon}</span>}
              <span className={cn('w-2 h-2 rounded-full', selectedPersona.color)} />
              <span className="font-medium">{selectedPersona.name}</span>
            </div>
            <p className="text-sm text-muted-foreground">
              {selectedPersona.description}
            </p>
          </div>
          
          <h3 className="font-medium mb-2">What I Can Do</h3>
          <div className="space-y-2">
            <div className="p-2 rounded bg-gray-600/10 flex items-center gap-2 ai-hover-lift">
              <div className="bg-gray-600/20 p-1 rounded">
                <Lightbulb className="h-3 w-3 text-gray-400" />
              </div>
              <span className="text-xs">Clarify Product Vision</span>
            </div>
            <div className="p-2 rounded bg-gray-600/10 flex items-center gap-2 ai-hover-lift">
              <div className="bg-gray-700/20 p-1 rounded">
                <Zap className="h-3 w-3 text-gray-400" />
              </div>
              <span className="text-xs">Develop Actionable Plans</span>
            </div>
            <div className="p-2 rounded bg-gray-600/10 flex items-center gap-2 ai-hover-lift">
              <div className="bg-black/20 p-1 rounded">
                <Brain className="h-3 w-3 text-gray-400" />
              </div>
              <span className="text-xs">Strategic Questioning</span>
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="memory" className="m-0 p-4 h-full">
          <h3 className="font-medium mb-2">Project Memory</h3>
          <div className="p-3 rounded-lg bg-gray-600/10 mb-2">
            <div className="text-sm font-medium mb-1">Current Session</div>
            <div className="text-xs text-muted-foreground">
              {messages.length - initialMessages.length} user message(s) in this conversation
            </div>
          </div>
          <h3 className="font-medium mb-2 mt-4">Quick Actions</h3>
          <div className="space-y-2">
            <Button variant="outline" className="w-full justify-start text-xs border-gray-600/30 hover:bg-gray-600/20 ai-hover-lift">
              <History className="h-3 w-3 mr-2" />
              Save this conversation
            </Button>
            <Button 
              variant="outline" 
              className="w-full justify-start text-xs border-gray-600/30 hover:bg-gray-600/20 ai-hover-lift"
              onClick={handleClearChat}
            >
              <X className="h-3 w-3 mr-2" />
              Start fresh
            </Button>
          </div>
        </TabsContent>
        <TabsContent value="history" className="m-0 p-4 h-full">
          <h3 className="font-medium mb-2">Project History</h3>
          <div className="text-xs text-muted-foreground mb-4">
            Your completed projects will appear here
          </div>
        </TabsContent>
        <TabsContent value="settings" className="m-0 p-4 h-full">
          <h3 className="font-medium mb-2">Preferences</h3>
          <div className="text-xs text-muted-foreground">
            Currently using the {selectedPersona.name} persona.
          </div>
        </TabsContent>
      </div>
    </Tabs>
  );

  const MobileSidebar = () => (
    <Drawer open={isMobile && sidebarOpen} onOpenChange={setSidebarOpen}>
      <DrawerTrigger asChild>
        {isMobile && (
          <Button
            variant="outline"
            size="icon"
            className="fixed top-4 right-4 z-50 bg-background/50 backdrop-blur-lg border-gray-600/30"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={18} />
          </Button>
        )}
      </DrawerTrigger>
      <DrawerContent className="h-[80vh]">
        <div className="px-4 py-2">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-lg">Assistant Settings</h3>
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)}>
              <X size={18} />
            </Button>
          </div>
          <SidebarContent />
        </div>
      </DrawerContent>
    </Drawer>
  );

  return (
    <TooltipProvider>
      <div className={cn(
        "flex h-screen overflow-hidden antialiased text-foreground bg-gradient-to-br from-gray-900 via-gray-950 to-black",
        "transition-all duration-300 ease-in-out"
      )}>
        
        {!isMobile && (
          <div className={cn(
            "bg-gray-800/30 border-r border-gray-700/50 shadow-2xl transition-all duration-300 ease-in-out",
            sidebarOpen ? "w-80 p-0" : "w-0 p-0"
          )}>
            {sidebarOpen && <SidebarContent />}
          </div>
        )}

        <div className="flex-1 flex flex-col relative bg-black/30">
          {/* Header */}
          <header className="bg-gray-900/30 backdrop-blur-md border-b border-gray-700/50 p-3 flex items-center justify-between h-16 z-10">
            <div className="flex items-center">
              {!isMobile && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="icon" onClick={toggleSidebar} className="mr-2">
                      {sidebarOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>{sidebarOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}</TooltipContent>
                </Tooltip>
              )}
              <AIAvatar persona={selectedPersona} size="sm" />
              <div className="ml-2">
                <h1 className="text-sm font-medium">{selectedPersona.name}</h1>
                <p className="text-xs text-green-400">Online</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm" className="border-gray-600/50 hover:bg-gray-700/30">
                    <Wand2 size={14} className="mr-1.5" /> Change Persona
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-gray-800 border-gray-700 text-foreground">
                  <PersonaSelector
                    personas={availablePersonas.map(toSelectorPersona)}
                    selectedPersona={toSelectorPersona(selectedPersona)} // Pass the selectedPersona object
                    onSelect={(persona) => { // The persona object is received here
                      const newPersona = availablePersonas.find(p => p.id === persona.id);
                      if (newPersona) {
                        setSelectedPersona(newPersona);
                        setMessages([
                          {
                            id: '1',
                            content: `👋 Switched to ${newPersona.name}. How can I assist you?`,
                            role: 'assistant',
                            timestamp: new Date().toISOString(),
                            emotion: 'happy'
                          }
                        ]);
                        toast({
                          title: "Persona Changed!",
                          description: `Now chatting with ${newPersona.name}.`,
                          duration: 3000
                        });
                      }
                    }}
                  />
                </DialogContent>
              </Dialog>
            </div>
          </header>

          {/* Chat Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-black/10 to-transparent">
            {messages.map((msg, index) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                isLastMessage={index === messages.length - 1}
                isAIThinking={isAIThinking && msg.role === 'assistant' && index === messages.length - 1}
                persona={msg.role === 'assistant' ? selectedPersona : undefined}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-700/50 p-4 bg-gray-900/30 backdrop-blur-md">
            <ChatInput 
              onSendMessage={handleSendMessage} 
              isAIThinking={isAIThinking} 
              placeholder={isAwaitingYesNo ? "Answer yes/no or provide details..." : `Chat with ${selectedPersona.name}...`}
            />
          </div>
        </div>

        {isMobile && <MobileSidebar />}
      </div>
    </TooltipProvider>
  );
};

export default ChatInterface;
