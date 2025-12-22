import google.generativeai as genai
import json
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiService:
    @staticmethod
    def generate_soap_note(transcript: str) -> dict:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        You are a clinical assistant. Given the following transcript of a medical consultation, 
        generate a structured SOAP note in JSON format.
        
        Transcript:
        {transcript}
        
        JSON Structure:
        {{
            "subjective": "...",
            "objective": "...",
            "assessment": "...",
            "plan": "..."
        }}
        
        Return ONLY the raw JSON.
        """
        
        response = model.generate_content(prompt)
        
        try:
            # Clean response if it contains markdown code blocks
            res_text = response.text.strip()
            if res_text.startswith("```"):
                res_text = res_text.split("```json")[-1].split("```")[0].strip()
            
            return json.loads(res_text)
        except Exception as e:
            print(f"Failed to parse Gemini response: {e}")
            return {
                "subjective": "Error generating note",
                "objective": "Error generating note",
                "assessment": "Error generating note",
                "plan": "Error generating note"
            }
