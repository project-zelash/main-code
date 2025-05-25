import React, { useState, useEffect, useRef, Dispatch, SetStateAction } from 'react';
import { cn } from '@/lib/utils';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Settings, Info, History, Brain, Sparkles, X, Menu, Zap, Wand2, ChevronLeft, ChevronRight, Lightbulb } from 'lucide-react';
import ChatInput from '@/components/ChatInput';
import MessageBubble from '@/components/MessageBubble';
import AIAvatar from '@/components/AIAvatar';
import PersonaSelector from '@/components/PersonaSelector';
import { type AIPersona as PersonaSelectorAIPersona } from '@/components/PersonaSelector';
import { getClarifyingQuestions, generateProductPlan, reviseProductPlan } from '../lib/gemini'; // Added reviseProductPlan
import { Message } from '../types/chat';
import { AIPersona } from '@/types/persona'; // Main persona type - CORRECTED PATH
import { Button } from '@/components/ui/button';
import { Drawer, DrawerTrigger, DrawerContent } from '@/components/ui/drawer';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip';
import { Dialog, DialogTrigger, DialogContent } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { useIsMobile } from '@/hooks/use-mobile';

interface ChatInterfaceProps {}

// Copied from gemini.ts to avoid import issues if gemini.ts ever needs to import from here.
// This is the system prompt for the plan generation phase.
const PLAN_GENERATION_SYSTEM_PROMPT = `You are the world’s most insightful and capable product planner. Your expertise lies in transforming abstract or imaginative product ideas—whether for a web app, mobile app, or a full end-to-end system—into clear, actionable, and innovative product plans.

You will be provided with:
1.  The user's original product idea.
2.  A set of yes/no questions that were posed to the user.
3.  The user's corresponding yes/no answers to these questions.

**Instructions for Plan Generation:**
1.  Synthesize all the provided information (initial idea and Q&A) into a coherent product plan.
2.  First, present this plan to the user in a clear, readable, natural language format. This part should be a comprehensive summary.
3.  After presenting the natural language plan, your **VERY NEXT and FINAL response** MUST be the complete product plan formatted as a single JSON object. Do not add any conversational text before or after this JSON block.
4.  The JSON should be structured logically, for example:
    {
      "productName": "User's Product Idea (or a refined name based on Q&A)",
      "targetAudience": "...",
      "coreFeatures": ["...", "...", "..."],
      "keyDifferentiators": ["...", "..."],
      "monetizationStrategy": "(if discussed, or 'To be determined')",
      "technologyStackConsiderations": "(if discussed, or 'To be determined')",
      "nonFunctionalRequirements": ["Scalability: ...", "Security: ...", "Usability: ..."],
      "userStories": [
        {"role": "As a [user type]", "action": "I want to [goal]", "reason": "so that [benefit]"},
      ],
      "futureConsiderations": ["...", "..."],
      "summary": "A brief overview of the refined product concept."
    }
    Ensure the JSON is valid. The fields in the example are illustrative; include fields that are relevant based on the information gathered.

Your primary goal is to help the user clarify their vision and develop an actionable product plan. Do not ask further questions in this phase; generate the plan based on the information you have.`

const productStrategistPersona: AIPersona = {
  id: 'product-strategist',
  name: 'Product Strategist',
  description: 'Helps you refine product ideas into actionable plans.',
  icon: <Lightbulb size={16} />,
  color: 'bg-blue-500',
  avatarUrl: '/placeholder.svg',
  systemInstruction: PLAN_GENERATION_SYSTEM_PROMPT, // This is for the plan generation step
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
    id: 'welcome-1',
    content: `Welcome to Zelash! I'm your Product Strategist. To begin, please describe the product idea you'd like to develop.`,
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

type ChatPhase = 
  | 'awaiting_idea' 
  | 'generating_questions' 
  | 'awaiting_question_answer' 
  | 'generating_plan' 
  | 'awaiting_plan_feedback' // Changed from presenting_plan, initial plan is shown, user can accept or request changes
  | 'revising_plan' 
  | 'plan_finalized' 
  | 'error_state';

const ChatInterfaceComponent: React.FC<ChatInterfaceProps> = () => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isAIThinking, setIsAIThinking] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState<AIPersona>(productStrategistPersona);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  const isMobile = useIsMobile();
  
  const [chatPhase, setChatPhase] = useState<ChatPhase>('awaiting_idea');
  const [currentProductIdea, setCurrentProductIdea] = useState<string | null>(null);
  const [questionsForUser, setQuestionsForUser] = useState<string[]>([]);
  const [answersFromUser, setAnswersFromUser] = useState<Record<string, boolean>>({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);
  const [totalQuestionsCount, setTotalQuestionsCount] = useState<number>(0);
  const [currentPlan, setCurrentPlan] = useState<{ text: string; json: object } | null>(null);

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
    if (!messageContent.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: messageContent, 
      role: 'user',
      timestamp: new Date().toISOString(),
    };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    
    if (chatPhase === 'awaiting_idea') {
      const lowerCaseIdea = messageContent.toLowerCase();
      const ideaLength = messageContent.trim().length;

      // Check for vague ideas
      if (ideaLength < 15 || lowerCaseIdea === "hi" || lowerCaseIdea === "hello" || lowerCaseIdea === "hey" || lowerCaseIdea === "yo") {
        const promptElaboration: Message = {
          id: 'elaborate-' + Date.now(),
          content: "That's a start! To help me understand, could you please provide a more detailed description of your product idea? What problem does it solve, or what does it aim to achieve?",
          role: 'assistant',
          timestamp: new Date().toISOString(),
          emotion: 'confused',
        };
        setMessages(prev => [...prev, promptElaboration]);
        return; // Stay in awaiting_idea phase
      }

      // Check for overly complex ideas
      const complexityKeywords = ["ml model", "web3", "blockchain", "artificial intelligence", "deep learning", "neural network", "crypto", "smart contract"];
      const largeScaleKeywords = ["global scale", "billions of users", "worldwide platform", "enterprise grade for fortune 500"];
      
      let isTooComplex = false;
      for (const keyword of complexityKeywords) {
        if (lowerCaseIdea.includes(keyword)) {
          isTooComplex = true;
          break;
        }
      }
      if (!isTooComplex) {
        for (const keyword of largeScaleKeywords) {
          if (lowerCaseIdea.includes(keyword)) {
            isTooComplex = true;
            break;
          }
        }
      }

      if (isTooComplex) {
        const complexIdeaMessage: Message = {
          id: 'complex-idea-' + Date.now(),
          content: "That sounds like a very ambitious and potentially complex project! While I can help plan many types of software, developing a full end-to-end solution involving advanced AI/ML, Web3, or massive global scale might be beyond the scope of what I can effectively help you plan in detail right now. Could we perhaps focus on a simpler core concept or a more specific, manageable part of this idea?",
          role: 'assistant',
          timestamp: new Date().toISOString(),
          emotion: 'concerned',
        };
        setMessages(prev => [...prev, complexIdeaMessage]);
        return; // Stay in awaiting_idea phase
      }

      setCurrentProductIdea(messageContent);
      setChatPhase('generating_questions');
      setIsAIThinking(true);
      setAnswersFromUser({});
      setCurrentQuestionIndex(0);
      setTotalQuestionsCount(0);
      setCurrentPlan(null); // Reset any previous plan

      const thinkingMsgForQuestions: Message = { // Renamed variable
        id: 'thinking-questions-' + Date.now(),
        content: 'Great idea! Thinking of some clarifying questions for you...',
        role: 'assistant',
        timestamp: new Date().toISOString(),
        isLoading: true,
      };
      setMessages((prev) => [...prev, thinkingMsgForQuestions]);

      try {
        const generatedQuestions = await getClarifyingQuestions(messageContent);
        setMessages((prev) => prev.filter(m => m.id !== thinkingMsgForQuestions.id)); // Use renamed variable

        if (generatedQuestions && generatedQuestions.length > 0) {
          setQuestionsForUser(generatedQuestions);
          setTotalQuestionsCount(generatedQuestions.length);
          
          // Present the first question
          const firstQuestionText = generatedQuestions[0];
          const progressIndicator = `(Question 1 of ${generatedQuestions.length})`;
          const firstQuestionMessage: Message = {
            id: `question-${Date.now()}-0`,
            content: `${progressIndicator} ${firstQuestionText}`,
            role: 'assistant',
            timestamp: new Date().toISOString(),
            isQuestion: true,
            questionId: `q-${Date.now()}-0`,
          };
          setMessages((prev) => [...prev, firstQuestionMessage]);
          setChatPhase('awaiting_question_answer');
          toast({ title: "Questions Ready!", description: "Please answer the first question below." });

        } else {
          const noQuestionsMessage: Message = {
            id: 'no-questions-' + Date.now(),
            content: "I couldn't generate specific questions for that idea. Could you perhaps elaborate a bit more, or provide a different angle?",
            role: 'assistant',
            timestamp: new Date().toISOString(),
            emotion: 'confused',
          };
          setMessages((prev) => [...prev, noQuestionsMessage]);
          setChatPhase('awaiting_idea');
        }
      } catch (err: any) { // Changed variable name from error to err
        console.error("Failed to get clarifying questions:", err);
        setMessages((prev) => prev.filter(m => m.id !== thinkingMsgForQuestions.id)); // Use renamed variable
        const errorMessage: Message = {
          id: 'error-questions-' + Date.now(),
          content: `Error generating questions: ${err.message || 'Please try again.'}`,
          role: 'assistant',
          timestamp: new Date().toISOString(),
          emotion: 'concerned',
        };
        setMessages((prev) => [...prev, errorMessage]);
        setChatPhase('error_state');
      } finally {
        setIsAIThinking(false);
      }
    } else if (chatPhase === 'awaiting_question_answer') {
      const clarificationMessage: Message = {
        id: 'clarification-' + Date.now(),
        content: "Please use the 'Yes' or 'No' buttons to answer the current question.",
        role: 'assistant',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, clarificationMessage]);
    } else if (chatPhase === 'awaiting_plan_feedback') {
      const lowerCaseContent = messageContent.toLowerCase();
      if (lowerCaseContent.includes('accept') || lowerCaseContent.includes('looks good') || lowerCaseContent.includes('finalize')) {
        if (!currentPlan) {
          const noPlanMessage: Message = {
            id: 'error-no-plan-to-finalize-' + Date.now(),
            content: "There isn't a current plan to finalize. Let's generate one first!",
            role: 'assistant',
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, noPlanMessage]);
          return;
        }
        // Send plan JSON to backend for detailed technical planning
        setChatPhase('fetching_detailed_plan');
        const loadingMessage: Message = {
          id: 'loading-detailed-plan-' + Date.now(),
          content: 'Generating a detailed technical plan, please wait...',
          role: 'assistant',
          timestamp: new Date().toISOString(),
          isLoading: true,
        };
        setMessages(prev => [...prev, loadingMessage]);
        try {
          const response = await fetch('/api/meta-planner/detailed-plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan: currentPlan.json }),
          });
          const detailedPlan = await response.json();
          // Remove loading indicator
          setMessages(prev => prev.filter(m => m.id !== loadingMessage.id));
          // Show detailed plan JSON
          const detailedPlanMessage: Message = {
            id: 'detailed-plan-' + Date.now(),
            content: JSON.stringify(detailedPlan, null, 2),
            role: 'assistant',
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, detailedPlanMessage]);
        } catch (err: any) {
          // Handle fetch error
          const errorMessage: Message = {
            id: 'error-detailed-plan-' + Date.now(),
            content: `Failed to generate detailed plan: ${err.message || 'Unknown error'}`,
            role: 'assistant',
            timestamp: new Date().toISOString(),
            emotion: 'concerned',
          };
          setMessages(prev => [...prev, errorMessage]);
        } finally {
          // Finalize and reset for next idea
          const finalizedMessage: Message = {
            id: 'plan-finalized-' + Date.now(),
            content: 'Detailed plan generated and saved. You can start a new idea now.',
            role: 'assistant',
            timestamp: new Date().toISOString(),
            emotion: 'happy',
          };
          setMessages(prev => [...prev, finalizedMessage]);
          setCurrentProductIdea(null);
          setAnswersFromUser({});
          setCurrentQuestionIndex(0);
          setQuestionsForUser([]);
          setCurrentPlan(null);
          setChatPhase('awaiting_idea');
        }
        return; // Exit after handling acceptance
       } else if (lowerCaseContent.includes('yes') || lowerCaseContent.includes('no')) {
         // existing branch for revising plan
       }
    } else if (chatPhase === 'revising_plan') {
      const thinkingMsgForRevision: Message = { // Renamed variable
        id: 'thinking-revision-' + Date.now(),
        content: 'Got your feedback! Revising the plan...',
        role: 'assistant',
        timestamp: new Date().toISOString(),
        isLoading: true,
      };
      setMessages((prev) => [...prev, thinkingMsgForRevision]);

      try {
        const { planText: revisedPlanText, planJson: revisedPlanJson } = await reviseProductPlan(
          currentPlan.json,
          messageContent, 
          currentProductIdea,
          answersFromUser
        );
        setMessages((prev) => prev.filter(m => m.id !== thinkingMsgForRevision.id)); // Use renamed variable

        setCurrentPlan({ text: revisedPlanText, json: revisedPlanJson });

        const revisedPlanTextMessage: Message = {
          id: 'revised-plan-text-' + Date.now(),
          content: revisedPlanText || "Here is the revised plan:",
          role: 'assistant',
          timestamp: new Date().toISOString(),
          planText: revisedPlanText,
        };
        const revisedPlanJsonMessage: Message = {
          id: 'revised-plan-json-' + Date.now(),
          content: "Updated structured JSON version of the plan:",
          role: 'assistant',
          timestamp: new Date().toISOString(),
          planJson: revisedPlanJson,
        };
        const feedbackPromptMessage: Message = {
          id: 'feedback-prompt-revised-' + Date.now(),
          content: "What do you think of the revised plan? You can provide more changes, or type 'Looks good' or 'Accept plan' to finalize it.",
          role: 'assistant',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, revisedPlanTextMessage, revisedPlanJsonMessage, feedbackPromptMessage]);
        setChatPhase('awaiting_plan_feedback'); 

      } catch (err: any) { // Changed variable name from error to err
        console.error("Failed to revise product plan:", err);
        setMessages((prev) => prev.filter(m => m.id !== thinkingMsgForRevision.id)); // Use renamed variable
        const errorMessage: Message = {
          id: 'error-revision-' + Date.now(),
          content: `Error revising plan: ${err.message || 'Please try again.'}`,
          role: 'assistant',
          timestamp: new Date().toISOString(),
          emotion: 'concerned',
        };
        setMessages((prev) => [...prev, errorMessage]);
        setChatPhase('awaiting_plan_feedback'); // Go back to feedback phase on error
      } finally {
        setIsAIThinking(false);
      }
    } else if (chatPhase === 'plan_finalized') {
        const startNewMessage: Message = {
            id: 'plan-finalized-prompt-' + Date.now(),
            content: "Plan already finalized. Please describe a new product idea to begin.",
            role: 'assistant',
            timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, startNewMessage]);
    }
  };
  
  const handleAnswerSelect = async (questionMessageId: string, originalQuestionContentWithProgress: string, answer: boolean) => {
    const actualQuestionText = originalQuestionContentWithProgress.replace(/\\(Question \\d+ of \\d+\\) /i, '').trim();

    setMessages(prevMessages => 
      prevMessages.map(msg => 
        msg.id === questionMessageId ? { ...msg, answered: answer ? 'yes' : 'no', isQuestion: false } : msg
      )
    );

    const newAnswers = { ...answersFromUser, [actualQuestionText]: answer };
    setAnswersFromUser(newAnswers);

    const nextIdx = currentQuestionIndex + 1;
    setCurrentQuestionIndex(nextIdx);

    if (nextIdx < totalQuestionsCount && currentProductIdea) {
      const questionText = questionsForUser[nextIdx];
      const progressIndicator = `(Question ${nextIdx + 1} of ${totalQuestionsCount})`;
      const nextQuestionMessage: Message = {
        id: `question-${Date.now()}-${nextIdx}`,
        content: `${progressIndicator} ${questionText}`,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        isQuestion: true,
        questionId: `q-${Date.now()}-${nextIdx}`,
      };
      setMessages((prev) => [...prev, nextQuestionMessage]);
      // Chat phase remains 'awaiting_question_answer'
    } else if (nextIdx >= totalQuestionsCount && currentProductIdea) {
      setChatPhase('generating_plan');
      setIsAIThinking(true);
      const thinkingMsgForPlan: Message = { // Renamed variable
        id: 'thinking-plan-' + Date.now(),
        content: 'All questions answered! Generating your initial product plan...',
        role: 'assistant',
        timestamp: new Date().toISOString(),
        isLoading: true,
      };
      setMessages((prev) => [...prev, thinkingMsgForPlan]);

      try {
        const { planText, planJson } = await generateProductPlan(currentProductIdea, newAnswers); // Use newAnswers here
        setMessages((prev) => prev.filter(m => m.id !== thinkingMsgForPlan.id)); // Use renamed variable

        setCurrentPlan({ text: planText, json: planJson });

        const planTextMessage: Message = {
          id: 'plan-text-' + Date.now(),
          content: planText || "Here is your initial product plan:",
          role: 'assistant',
          timestamp: new Date().toISOString(),
          planText: planText,
        };
        const planJsonMessage: Message = {
          id: 'plan-json-' + Date.now(),
          content: "Here is the structured JSON version of the plan:", // Simplified message
          role: 'assistant',
          timestamp: new Date().toISOString(),
          planJson: planJson,
        };
        const feedbackPromptMessage: Message = {
            id: 'feedback-prompt-' + Date.now(),
            content: "What do you think of this initial plan? Please provide any feedback for changes, or type 'Looks good' or 'Accept plan' to finalize it.",
            role: 'assistant',
            timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, planTextMessage, planJsonMessage, feedbackPromptMessage]);
        setChatPhase('awaiting_plan_feedback');
        toast({ title: "Initial Product Plan Ready!", description: "Review your plan and provide feedback or accept it." });

      } catch (err: any) { // Changed variable name from error to err
        console.error("Failed to generate product plan:", err);
        setMessages((prev) => prev.filter(m => m.id !== thinkingMsgForPlan.id)); // Use renamed variable
        const errorMessage: Message = {
          id: 'error-plan-' + Date.now(),
          content: `Error generating plan: ${err.message || 'Please try again.'}`,
          role: 'assistant',
          timestamp: new Date().toISOString(),
          emotion: 'concerned',
        };
        setMessages((prev) => [...prev, errorMessage]);
        setChatPhase('error_state');
      } finally {
        setIsAIThinking(false);
      }
    }
  };

  const handleClearChat = () => {
    setMessages(initialMessages); 
    setCurrentProductIdea(null);
    setQuestionsForUser([]);
    setAnswersFromUser({});
    setCurrentQuestionIndex(0);
    setTotalQuestionsCount(0);
    setCurrentPlan(null);
    setChatPhase('awaiting_idea');
    toast({
      title: "Fresh start!",
      description: `Ready to strategize with the ${selectedPersona.name}.`,
      duration: 3000
    });
  };

  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev);
  };

  // SidebarContent and MobileSidebar are functional components and should return JSX or null.
  // The error "Type '() => void' is not assignable to type 'ReactNode'." suggests one of them might not be.
  // Ensuring they return valid ReactNode.
  const SidebarContent: React.FC = () => (
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
             <div className="p-2 rounded bg-gray-600/10 flex items-center gap-2 ai-hover-lift">
              <div className="bg-gray-600/20 p-1 rounded">
                <Sparkles className="h-3 w-3 text-gray-400" />
              </div>
              <span className="text-xs">Iterative Plan Revision</span>
            </div>
          </div>

          <h3 className="font-medium mb-2 mt-4">Current Phase</h3>
            <div className="p-2 rounded bg-gray-600/10 flex items-center gap-2">
                <div className="bg-gray-600/20 p-1 rounded">
                    <Sparkles className="h-3 w-3 text-gray-400" />
                </div>
                <span className="text-xs capitalize">{chatPhase.replace(/_/g, ' ')}</span>
            </div>
            {currentProductIdea && (
                <div className="mt-2 p-2 rounded bg-gray-600/10">
                    <p className="text-xs font-medium">Idea:</p>
                    <p className="text-xs text-muted-foreground truncate">{currentProductIdea}</p>
                </div>
            )}
        </TabsContent>
        <TabsContent value="memory" className="m-0 p-4 h-full">
          <h3 className="font-medium mb-2">Project Memory</h3>
          <div className="p-3 rounded-lg bg-gray-600/10 mb-2">
            <div className="text-sm font-medium mb-1">Current Session</div>
            <div className="text-xs text-muted-foreground">
              {messages.length - initialMessages.length} user message(s) in this conversation
            </div>
          </div>
          {currentPlan && (
            <div className="p-3 rounded-lg bg-gray-600/10 mb-2">
                <div className="text-sm font-medium mb-1">Current Plan Status</div>
                <div className="text-xs text-muted-foreground">
                    {chatPhase === 'plan_finalized' ? 'Plan Finalized' : 'Plan in Progress'}
                </div>
            </div>
          )}
          <h3 className="font-medium mb-2 mt-4">Quick Actions</h3>
          <div className="space-y-2">
            <Button variant="outline" className="w-full justify-start text-xs border-gray-600/30 hover:bg-gray-600/20 ai-hover-lift" onClick={() => toast({title: "Coming Soon!", description: "Saving conversations is on the roadmap."}) }>
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
            Your completed projects will appear here (feature coming soon!)
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

  const MobileSidebar: React.FC = () => (
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
              <AIAvatar aiPersona={selectedPersona} size="sm" />
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
                    selectedPersona={toSelectorPersona(selectedPersona)}
                    onSelect={(persona) => { 
                      const newPersona = availablePersonas.find(p => p.id === persona.id);
                      if (newPersona) {
                        setSelectedPersona(newPersona);
                        // Reset chat when persona changes to avoid phase conflicts
                        handleClearChat(); 
                        setMessages([
                          {
                            id: 'persona-switch-' + Date.now(),
                            content: `👋 Switched to ${newPersona.name}. How can I assist you?`,
                            role: 'assistant',
                            timestamp: new Date().toISOString(),
                          }
                        ]);
                      }
                    }}
                  />
                </DialogContent>
              </Dialog>
            </div>
          </header>

          {/* Chat messages area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-2">
            {messages.map((msg, index) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                isLastMessage={index === messages.length - 1}
                onAnswerSelect={handleAnswerSelect} 
              />
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat input area */}
          <div className="border-t border-gray-700/50 p-4 bg-gray-900/30 backdrop-blur-md">
            <ChatInput
              onSendMessage={handleSendMessage}
              isAIThinking={isAIThinking} // Corrected prop name from isAIThinking
            />
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
};

export default ChatInterfaceComponent;
