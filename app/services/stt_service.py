import assemblyai as aai
from app.core.config import settings

aai.settings.api_key = settings.ASSEMBLYAI_API_KEY

class AssemblyAIService:
    @staticmethod
    def transcribe_audio(audio_path: str) -> str:
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            punctuate=True,
            format_text=True
        )
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_path, config=config)
        
        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"Transcription failed: {transcript.error}")
            
        return transcript.text

    @staticmethod
    async def transcribe_audio_async(audio_path: str) -> str:
        # For simplicity in this demo, we'll use synchronous transcribe in a thread
        # In a production app, we'd use webhooks or polling
        import functools
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            functools.partial(AssemblyAIService.transcribe_audio, audio_path)
        )
