const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY; // Store this securely, e.g., in environment variables

interface GeminiResponse {
  candidates: Array<{
    content: {
      parts: Array<{
        text: string;
      }>;
      role: string;
    };
    finishReason: string;
    index: number;
    safetyRatings: Array<{
      category: string;
      probability: string;
    }>;
  }>;
  promptFeedback: {
    safetyRatings: Array<{
      category: string;
      probability: string;
    }>;
  };
}

export async function generateContentWithGemini(
  userPrompt: string,
  systemInstructionText?: string
): Promise<string> {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`; // Changed model to gemini-1.5-flash-latest

  const requestBody: any = {
    contents: [
      {
        role: "user",
        parts: [
          {
            text: userPrompt,
          },
        ],
      },
    ],
  };

  if (systemInstructionText) {
    requestBody.systemInstruction = {
      parts: [
        {
          text: systemInstructionText,
        },
      ],
    };
  }

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      console.error('Gemini API request failed. Status:', response.status, 'Body:', errorBody);
      let detailedError = errorBody;
      try {
        const parsedError = JSON.parse(errorBody);
        if (parsedError && parsedError.error && parsedError.error.message) {
          detailedError = parsedError.error.message;
        }
      } catch (e) { /* ignore parsing error, use raw text */ }
      throw new Error(`API Error (${response.status}): ${detailedError}`);
    }

    const data = (await response.json()) as GeminiResponse;

    if (data.candidates && data.candidates.length > 0 && data.candidates[0].content && data.candidates[0].content.parts && data.candidates[0].content.parts.length > 0) {
      return data.candidates[0].content.parts[0].text;
    } else if (data.promptFeedback?.safetyRatings?.some(rating => rating.probability !== 'NEGLIGIBLE' && rating.probability !== 'LOW')) {
      const blockedReason = data.promptFeedback.safetyRatings.find(rating => rating.probability !== 'NEGLIGIBLE' && rating.probability !== 'LOW');
      console.warn('Gemini API prompt blocked:', blockedReason);
      return `I'm sorry, I can't respond to that. Reason: Prompt was blocked due to ${blockedReason?.category}.`;
    } else {
      console.error('Unexpected Gemini API response structure:', data);
      return 'Sorry, I could not process the API response.';
    }
  } catch (error: any) {
    console.error('Error calling Gemini API:', error);
    return error.message && error.message.startsWith('API Error') ? error.message : 'Sorry, there was an error communicating with the AI.';
  }
}
