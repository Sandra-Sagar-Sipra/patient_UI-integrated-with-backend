import google.generativeai as genai
import json
import asyncio
from typing import List, Dict, Any
from app.core.config import settings

# Configure global API key
genai.configure(api_key=settings.GOOGLE_API_KEY)

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    @staticmethod
    @retry(
        stop=stop_after_attempt(5), # Increased attempts for quota
        wait=wait_exponential(multiplier=2, min=4, max=60), # Exponential backoff: 4s, 8s, 16s, 32s, 60s
        reraise=True
    )
    async def generate_soap_note_async(transcript_text: str, speaker_labels: List[Dict[str, Any]] = None, patient_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generates a structured SOAP note from the transcript using Gemini.
        Returns a dictionary matching the SOAP note schema.
        Includes robust retry logic for 429 Quota errors.
        """
        # Construct a speaker-aware transcript if labels are provided
        formatted_transcript = transcript_text
        if speaker_labels:
            formatted_lines = []
            for utter in speaker_labels:
                 # utter is expected to be a dict like {'speaker': 'A', 'text': '...', ...}
                 speaker = utter.get('speaker', 'Unknown')
                 text = utter.get('text', '')
                 formatted_lines.append(f"Speaker {speaker}: {text}")
            formatted_transcript = "\n".join(formatted_lines)
            
        # Format Patient Context for Prompt
        context_str = "Unknown"
        if patient_context:
            context_str = (
                f"Name: {patient_context.get('first_name', '')} {patient_context.get('last_name', '')}\n"
                f"Age: {patient_context.get('age', 'N/A')}\n"
                f"Gender: {patient_context.get('gender', 'N/A')}\n"
                f"Medical History/Notes: {patient_context.get('notes', 'None provided')}"
            )
            
        # Initialize Model (gemini-2.0-flash is available and efficient)
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config={"response_mime_type": "application/json"}
        )
        
        prompt = f"""
        You are an expert medical scribe. Your task is to analyze the following Doctor-Patient consultation transcript and generate a professional, structured SOAP note encoded as JSON.
        
        Patient Context:
        {context_str}
        
        Transcript:
        {formatted_transcript}
        
        Instructions:
        1. Analyze the transcript in the context of the patient's demographics and history.
        2. Extrapolate the Subjective, Objective, Assessment, and Plan sections.
        3. **STRICT GROUNDING**: Do NOT infer information not present in the audio. If a vital sign or detail is not explicitly stated or strongly implied by the transcript, do NOT invent it.
        4. **UNCERTAINTY**: If a term is ambiguous (e.g., "measure" vs "mention") or if the speaker is unclear, flag it in the "low_confidence" list.
        5. Identify any Risk Flags (e.g., Suicide risk, Severe allergies, Abuse).
        6. Return STRICTLY valid JSON. No markdown formatting.
        
        Required JSON Structure:
        {{
            "soap_note": {{
                "subjective": "Patient's presenting complaints, history of present illness...",
                "objective": "Observations, physical findings (if mentioned), vitals...",
                "assessment": "Diagnosis or differential diagnoses...",
                "plan": "Treatment plan, medications, follow-up..."
            }},
            "low_confidence": ["list", "of", "ambiguous", "terms"],
            "risk_flags": ["Risk 1", "Risk 2"] 
        }}
        """
        
        # Offload the blocking API call to a thread
        loop = asyncio.get_event_loop()
        
        try:
            print("   (Gemini) Sending request...")
            response = await loop.run_in_executor(
                None, 
                lambda: model.generate_content(prompt)
            )
        except Exception as e:
            # Check for quota errors to print explicit warning (Tenacity handles the retry)
            if "429" in str(e) or "quota" in str(e).lower() or "resource exhausted" in str(e).lower():
                print(f"   ⚠️ Quota Limit Hit (429). Retrying in background...")
            raise e
        
        try:
            # Parse JSON result
            result_json = json.loads(response.text)
            return result_json
        except json.JSONDecodeError:
            # Fallback if strict JSON fails (rare with response_mime_type set)
            print(f"JSON Decode Error. Raw response: {response.text}")
            # Attempt to clean potential markdown
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(cleaned_text)
            except:
                 raise Exception("Failed to generate valid JSON SOAP note")
        except Exception as e:
            raise Exception(f"Gemini generation failed: {str(e)}")
