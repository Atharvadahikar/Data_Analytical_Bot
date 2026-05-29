import os

from groq import Groq


class InsightAgent:

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def call_llm(self, prompt):

        if not self.client:
            return "Groq API key not configured."

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """
You are a business analytics assistant.

Explain insights for non-technical business users.

Rules:
- Do not use technical ML words.
- Avoid terms like correlation, cross-validation, encoding, variance, RMSE, multicollinearity.
- Use simple business language.
- Focus on sales, cost, pricing, risk, opportunities, and decisions.
- Give output in this format:

Executive Summary
- Simple point 1
- Simple point 2

Business Impact
- What this means for revenue, cost, or pricing

Risks
- What the business should be careful about

Recommendations
- Clear action steps

Keep it short, clean, and useful.
"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            return completion.choices[0].message.content

        except Exception as e:
            return f"Groq Error: {str(e)}"

    def summarize(self, context):

        prompt = f"""
Generate:

1. Executive Summary
2. Key Findings
3. Data Quality Issues
4. Business Insights
5. Model Improvement Suggestions
6. Next Steps

Context:

{context}
"""

        return self.call_llm(prompt)

    def answer(self, question, context):

        prompt = f"""
Context:

{context}

Question:

{question}

Answer clearly using only context.
"""

        return self.call_llm(prompt)
