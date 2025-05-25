/**
 * Handles interactions with the Gemini API for Zelash.
 */

const GEMINI_MODEL_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent";

interface GeminiResponsePart {
  text?: string;
}

interface GeminiResponseContent {
  parts: GeminiResponsePart[];
  role: string;
}

interface GeminiCandidate {
  content: GeminiResponseContent;
  finishReason: string;
  index: number;
  safetyRatings: Array<{ category: string; probability: string }>;
}

interface GeminiResponse {
  candidates: GeminiCandidate[];
  promptFeedback?: {
    safetyRatings: Array<{ category: string; probability: string }>;
  };
}

/**
 * System prompt for generating clarifying questions.
 */
const QUESTION_GENERATION_PROMPT = `You are the world’s most insightful and capable product planner. Your expertise lies in transforming abstract or imaginative product ideas into clear, actionable, and innovative product plans.

The user will provide their initial product idea. Your task is to generate a set of clarifying yes/no questions to help them refine their vision.

**Instructions for Question Generation:**
1.  Based on the user\'s initial product idea, generate a JSON array containing up to 10 strategic yes/no questions.
2.  The output MUST be ONLY the JSON array of questions. Do not include any other text before or after the JSON.
3.  The JSON structure should be: {"questions": ["Question 1?", "Question 2?", ...]}\n4.  Each question must be a simple yes/no question directly aimed at understanding the core aspects of the product (e.g., target audience, core features, key differentiators, monetization, technology preferences).
5.  Make no assumptions. The questions should help the user think through their idea.`;

/**
 * System prompt for generating the product plan.
 */
const PLAN_GENERATION_PROMPT = `You are the world’s most insightful and capable product planner. Your expertise lies in transforming abstract or imaginative product ideas—whether for a web app, mobile app, or a full end-to-end system—into clear, actionable, and innovative product plans.

You will be provided with:
1.  The user\'s original product idea.
2.  A set of yes/no questions that were posed to the user.
3.  The user\'s corresponding yes/no answers to these questions.

**Instructions for Plan Generation:**
1.  Synthesize all the provided information (initial idea and Q&A) into a coherent product plan.
2.  First, present this plan to the user in a clear, readable, natural language format. This part should be a comprehensive summary.
3.  After presenting the natural language plan, your **VERY NEXT and FINAL response** MUST be the complete product plan formatted as a single JSON object. Do not add any conversational text before or after this JSON block.
4.  The JSON should be structured logically, for example:
    {
      "productName": "User\'s Product Idea (or a refined name based on Q&A)",
      "targetAudience": "...",
      "coreFeatures": ["...", "...", "..."],
      "keyDifferentiators": ["...", "..."],
      "monetizationStrategy": "(if discussed, or \'To be determined\')",
      "technologyStackConsiderations": "(if discussed, or \'To be determined\')",
      "nonFunctionalRequirements": ["Scalability: ...", "Security: ...", "Usability: ..."],
      "userStories": [
        {"role": "As a [user type]", "action": "I want to [goal]", "reason": "so that [benefit]"
      }],
      "futureConsiderations": ["...", "..."],
      "summary": "A brief overview of the refined product concept."
    }
    Ensure the JSON is valid. The fields in the example are illustrative; include fields that are relevant based on the information gathered.

Your primary goal is to help the user clarify their vision and develop an actionable product plan. Do not ask further questions in this phase; generate the plan based on the information you have.`;

/**
 * System prompt for revising an existing product plan based on user feedback.
 */
const REVISE_PLAN_PROMPT = `You are an expert product plan refiner. You will be provided with:
1. The user\\\'s original product idea.
2. The user\\\'s answers to initial clarifying questions.
3. An existing JSON product plan that was generated based on the above.
4. User\\\'s textual feedback requesting changes to this existing plan.

**Your Task:**
1. Carefully analyze the user\\\'s feedback and the existing JSON plan.
2. Modify the existing JSON plan to incorporate the user\\\'s requested changes. Ensure the new plan remains coherent and well-structured.
3. Output a brief natural language summary highlighting the key changes made or a concise overview of the revised plan.
4. Following the natural language summary, your **VERY NEXT and FINAL response** MUST be the complete **revised product plan** formatted as a single JSON object. Do not add any conversational text before or after this JSON block.
5. The revised JSON should follow the same general structure as the original plan, adapting fields as necessary based on the feedback.

Example of expected output structure:
Summary of changes: We\\\'ve updated the target audience to include young professionals and added a feature for offline access.

{
  \\\"productName\\\": \\\"...\\\", // (possibly updated)
  \\\"targetAudience\\\": \\\"...\\\", // (reflecting changes)
  // ... other fields, updated as per feedback ...
  \\\"coreFeatures\\\": [\\\"...\\\", \\\"new feature based on feedback\\\", \\\"...\\\"],
  // ...
}
Ensure the output JSON is valid and complete.`;

function getApiKey(): string {
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error("VITE_GEMINI_API_KEY is not set in .env file. Please ensure it is configured correctly.");
  }
  return apiKey;
}

// Helper function to parse plan text and JSON from Gemini response
function parsePlanFromGeminiResponse(responseData: GeminiResponse): { planText: string; planJson: object } {
  if (responseData.candidates && responseData.candidates.length > 0) {
    const firstCandidate = responseData.candidates[0];
    if (firstCandidate.content && firstCandidate.content.parts.length > 0) {
      const combinedText = firstCandidate.content.parts.map(p => p.text || "").join("");
      let planText = "";
      let planJsonString = "{}"; // Default to empty JSON object

      // Regex to find a JSON block, possibly enclosed in ```json ... ```
      const jsonBlockRegex = /(?:```json)?\\s*(\\{\\s*[\\s\\S]*\\s*\\})\\s*(?:```)?/m;
      const match = combinedText.match(jsonBlockRegex);

      if (match && match[1]) {
        planJsonString = match[1].trim();
        const jsonStartIndex = combinedText.indexOf(match[0]);
        // Text before the JSON block is considered the plan text
        planText = combinedText.substring(0, jsonStartIndex).trim();
        
        // If planText is empty and JSON was at the start, check for text *after* the JSON block.
        // This handles cases where the LLM might put the summary after the JSON.
        if (!planText && jsonStartIndex === 0) {
          const textAfterJson = combinedText.substring(jsonStartIndex + match[0].length).trim();
          if (textAfterJson) {
              planText = textAfterJson;
              console.warn("JSON block was at the beginning. Text found *after* JSON is used as plan text.");
          }
        }
        // If no text before, and no text after, but JSON exists, planText remains empty.
        if (!planText) {
            planText = "Here is the structured product plan:"; // Default text if none is found
        }

      } else {
        // No clear JSON block found with the primary regex.
        // Treat the entire response as plan text and try a more general JSON search.
        planText = combinedText.trim();
        console.warn("Could not reliably extract a JSON block with primary regex. Entire response treated as text. Attempting a fallback JSON search.");
        const fallbackJsonMatch = combinedText.match(/(\\{\\s*[\\s\\S]*\\s*\\})/m); // Simpler regex for any JSON object
        if (fallbackJsonMatch && fallbackJsonMatch[1]) {
          try {
            JSON.parse(fallbackJsonMatch[1]); // Validate if it's actual JSON
            planJsonString = fallbackJsonMatch[1].trim();
            // Attempt to refine planText if JSON was found mid-text
            const heuristicJsonStartIndex = planText.indexOf(planJsonString);
            if (heuristicJsonStartIndex > 0) {
                planText = planText.substring(0, heuristicJsonStartIndex).trim();
            } else if (heuristicJsonStartIndex === 0) {
                // If JSON is at the very start of the fallback, what was planText?
                // It was the whole string. If we take JSON out, text might be after.
                const textAfterFallbackJson = combinedText.substring(planJsonString.length).trim();
                if(textAfterFallbackJson) planText = textAfterFallbackJson;
                else planText = "Here is the structured product plan:"; // Default if only JSON found
            }
          } catch (e) {
            console.warn("Fallback JSON search also failed to find or parse a valid JSON object.");
          }
        }
      }

      try {
        const planJson = JSON.parse(planJsonString);
        return { planText: planText || "Generated plan details below:", planJson };
      } catch (e) {
        console.error("Failed to parse extracted JSON string:", planJsonString, e);
        // Return text if available, and an error object for JSON part
        const errorJson = { error: "Failed to parse JSON plan", details: e instanceof Error ? e.message : String(e), originalJsonString: planJsonString };
        if (planText) {
          console.warn("Returning text plan only due to JSON parsing error.");
          return { planText, planJson: errorJson };
        }
        // If no plan text either, this is a more critical failure of parsing.
        throw new Error("Failed to parse plan JSON (invalid JSON), and no text plan available.");
      }
    }
  }
  console.error("No suitable content found in Gemini API response for plan generation/revision.", responseData);
  throw new Error("Failed to process plan from Gemini API: No suitable content.");
}

/**
 * Generates clarifying questions based on the user\'s product idea.
 * @param productIdea The user\'s initial product idea.
 * @returns A promise that resolves to an array of question strings.
 */
export async function getClarifyingQuestions(productIdea: string): Promise<string[]> {
  const apiKey = getApiKey();
  const apiUrl = `${GEMINI_MODEL_BASE_URL}?key=${apiKey}`;

  try {
    const requestBody = {
      contents: [
        {
          parts: [
            { text: QUESTION_GENERATION_PROMPT },
            { text: `\n\nUser\'s Product Idea: ${productIdea}` },
          ],
        },
      ],
      generationConfig: {
        temperature: 0.5,
      },
    };

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      console.error("Gemini API Error Response (getClarifyingQuestions):", errorBody);
      throw new Error(`Gemini API request failed with status ${response.status}. Check console for details.`);
    }

    const responseData: GeminiResponse = await response.json();

    if (responseData.candidates && responseData.candidates.length > 0) {
      const firstCandidate = responseData.candidates[0];
      if (firstCandidate.content && firstCandidate.content.parts.length > 0) {
        const part = firstCandidate.content.parts[0];
        if (part.text) {
          try {
            const cleanedText = part.text.trim().replace(/^```json/, '').replace(/```$/, '').trim();
            const parsedJson = JSON.parse(cleanedText);
            if (parsedJson && Array.isArray(parsedJson.questions)) {
              return parsedJson.questions;
            }
            console.error("Gemini API response for questions was not in the expected format (missing questions array):", part.text);
            throw new Error("Failed to parse questions from Gemini API: Missing 'questions' array.");
          } catch (e) {
            console.error("Gemini API response for questions was not valid JSON:", part.text, e);
            throw new Error("Failed to parse questions from Gemini API: Invalid JSON.");
          }
        }
      }
    }
    console.error("No suitable content found in Gemini API response for questions:", responseData);
    throw new Error("Failed to get clarifying questions from Gemini API: No suitable content.");

  } catch (error) {
    console.error("Error in getClarifyingQuestions:", error);
    if (error instanceof Error) throw error;
    throw new Error("An unknown error occurred in getClarifyingQuestions.");
  }
}

/**
 * Generates a product plan based on the user\'s idea and answers to questions.
 * @param productIdea The user\'s initial product idea.
 * @param answers A record of questions and their boolean answers.
 * @returns A promise that resolves to an object containing the plan text and plan JSON.
 */
export async function generateProductPlan(productIdea: string, answers: Record<string, boolean>): Promise<{ planText: string; planJson: object }> {
  const apiKey = getApiKey();
  const apiUrl = `${GEMINI_MODEL_BASE_URL}?key=${apiKey}`;

  try {
    const qnaString = Object.entries(answers)
      .map(([question, answer]) => `Q: ${question}\nA: ${answer ? 'Yes' : 'No'}`)
      .join("\n\n");

    const requestBody = {
      contents: [
        {
          parts: [
            { text: PLAN_GENERATION_PROMPT },
            { text: `\n\nUser\'s Original Product Idea: ${productIdea}` },
            { text: `\n\nUser\'s Answers to Clarifying Questions:\n${qnaString}` },
          ],
        },
      ],
      generationConfig: {
        temperature: 0.6,
      },
    };

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      console.error("Gemini API Error Response (generateProductPlan):", errorBody);
      throw new Error(`Gemini API request failed with status ${response.status}. Check console for details.`);
    }

    const responseData: GeminiResponse = await response.json();
    return parsePlanFromGeminiResponse(responseData);

  } catch (error) {
    console.error("Error in generateProductPlan:", error);
    if (error instanceof Error) throw error;
    throw new Error("An unknown error occurred in generateProductPlan.");
  }
}

/**
 * Revises an existing product plan based on user feedback.
 * @param originalPlanJson The existing JSON representation of the plan.
 * @param userFeedback Textual feedback from the user detailing requested changes.
 * @param productIdea The original product idea (for context).
 * @param answers The original Q&A (for context).
 * @returns A promise that resolves to an object containing the revised plan text and plan JSON.
 */
export async function reviseProductPlan(
  originalPlanJson: object,
  userFeedback: string,
  productIdea: string,
  answers: Record<string, boolean>
): Promise<{ planText: string; planJson: object }> {
  const apiKey = getApiKey();
  const apiUrl = `${GEMINI_MODEL_BASE_URL}?key=${apiKey}`;

  try {
    const qnaString = Object.entries(answers)
      .map(([question, answer]) => `Q: ${question}\\nA: ${answer ? 'Yes' : 'No'}`)
      .join("\\n\\n");

    const requestBody = {
      contents: [
        {
          parts: [
            { text: REVISE_PLAN_PROMPT },
            { text: `\\n\\nUser\\\'s Original Product Idea: ${productIdea}` },
            { text: `\\n\\nUser\\\'s Answers to Clarifying Questions:\\n${qnaString}` },
            { text: `\\n\\nExisting JSON Plan to Revise:\\n\`\`\`json\\n${JSON.stringify(originalPlanJson, null, 2)}\\n\`\`\`` },
            { text: `\\n\\nUser\\\'s Feedback for Revision:\\n${userFeedback}` },
          ],
        },
      ],
      generationConfig: {
        temperature: 0.5, // Slightly lower temperature for revision to be more faithful
      },
    };

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      console.error("Gemini API Error Response (reviseProductPlan):", errorBody);
      throw new Error(`Gemini API request failed during plan revision (status ${response.status}). Check console.`);
    }

    const responseData: GeminiResponse = await response.json();
    return parsePlanFromGeminiResponse(responseData);

  } catch (error) {
    console.error("Error in reviseProductPlan:", error);
    if (error instanceof Error) throw error;
    throw new Error("An unknown error occurred in reviseProductPlan.");
  }
}

// Example Usage (Commented out by default - uncomment and run `bun run dev` then check console)
/*
async function testGeminiFunctions() {
  console.log("Testing Zelash Gemini API functions...");
  // Ensure VITE_GEMINI_API_KEY is in your .env file
  if (!import.meta.env.VITE_GEMINI_API_KEY) {
    console.error("VITE_GEMINI_API_KEY is not set. Aborting test.");
    return;
  }
  console.log("API Key found.");

  try {
    console.log("\n--- Testing getClarifyingQuestions ---");
    const productIdea = "An AI-powered app to help people learn new languages through interactive stories.";
    console.log(`Product Idea: ${productIdea}`);
    const questions = await getClarifyingQuestions(productIdea);
    console.log("Generated Questions:", questions);

    if (questions && questions.length > 0) {
      console.log("\n--- Testing generateProductPlan ---");
      const answers: Record<string, boolean> = {};
      // Simulate answers for the first few questions
      questions.slice(0, Math.min(5, questions.length)).forEach((q, i) => {
        answers[q] = i % 2 === 0; // Alternate yes/no
      });
      console.log("Simulated Answers:", answers);

      if (Object.keys(answers).length > 0) {
        const plan = await generateProductPlan(productIdea, answers);
        console.log("\nGenerated Plan Text:\n", plan.planText);
        console.log("\nGenerated Plan JSON:\n", JSON.stringify(plan.planJson, null, 2));

        if (plan.planJson && !(plan.planJson as any).error) {
          console.log("\n--- Testing reviseProductPlan ---");
          const userFeedback = "Actually, let\\\'s target students instead of professionals, and add a gamification feature.";
          console.log("User Feedback for Revision:", userFeedback);
          const revisedPlan = await reviseProductPlan(plan.planJson, userFeedback, productIdea, answers);
          console.log("\nRevised Plan Text:\n", revisedPlan.planText);
          console.log("\nRevised Plan JSON:\n", JSON.stringify(revisedPlan.planJson, null, 2));
        }

      } else {
        console.log("Skipping plan generation test as no answers were simulated.");
      }
    } else {
      console.log("Skipping plan generation test as no questions were generated.");
    }
  } catch (error) {
    console.error("\n--- Test Failed ---", error);
  }
}

// To run the test, open your browser console when the app is running
// and call testGeminiFunctions() or uncomment the line below.
// testGeminiFunctions();
*/
