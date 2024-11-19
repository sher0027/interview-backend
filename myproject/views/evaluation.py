from myproject.utils.format import download_s3_file, parse_s3_url
from myproject.utils.openai import get_openai_response
import soundfile as sf
import librosa
import re
from io import BytesIO
from django.http import JsonResponse
from myproject.utils.analysis import intensity_calculation, pause_per_minute_calculation, pitch_calculation
from rest_framework.views import APIView
from myproject.repositories.record import RecordRepository
from myproject.repositories.evaluation import EvaluationRepository

class EvaluationView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.record_repo = RecordRepository()
        self.eval_repo = EvaluationRepository()

    def get(self, request, eid, seq=None, *args, **kwargs):
        try:
            if seq:
                evaluation = self.eval_repo.get_evaluation(eid, seq)
                if not evaluation:
                    return JsonResponse({"error": "Evaluation not found"}, status=404)
                return JsonResponse(evaluation, status=200)
            else:
                evaluations = self.eval_repo.get_all_evaluations(eid)
                if not evaluations:
                    return JsonResponse({"error": "No evaluation found for the given eid"}, status=404)
                return JsonResponse({"evaluations": evaluations}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def post(self, request, eid, *args, **kwargs):
        """
        Trigger evaluation for a specific record (acoustic and content).
        """
        try:
            records = self.record_repo.get_all_records(eid)
            if not records:
                return JsonResponse({"error": "Records not found."}, status=404)
            
            acoustic_results = []
            content_results = []

            for record in records:
                seq = record.get('seq')
                print(f"Start evaluation for sequence: {seq}")
                s3_url = record.get('s3_url')
                if s3_url:
                    acoustic_result = self._analyze_acoustic(s3_url)
                    self.eval_repo.save_acoustic_evaluation(eid, seq, acoustic_result)
                    acoustic_results.append({f"seq_{seq}": acoustic_result})

                transcript = record.get('transcript')
                if transcript:
                    content_result = self._analyze_content(transcript)
                    self.eval_repo.save_content_evaluation(eid, seq, content_result)
                    content_results.append({f"seq_{seq}": content_result})

            return JsonResponse({"message": "Evaluation completed successfully."}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    def _analyze_acoustic(self, s3_url):
        """
        Analyze acoustic features of an audio file directly from S3 using Boto3.
        """
        try:
            bucket_name, object_key = parse_s3_url(s3_url)
            audio_data = download_s3_file(bucket_name, object_key)

            audio_array, sample_rate = sf.read(BytesIO(audio_data))
            audio_duration_minutes = librosa.get_duration(y=audio_array, sr=sample_rate) / 60

            intensity = intensity_calculation(audio_array)
            pitch = pitch_calculation(audio_array)
            pauses = pause_per_minute_calculation(audio_array, sample_rate, audio_duration_minutes)

            evaluation_result = {
                "intensity": intensity,
                "pitch": pitch,
                "pauses": pauses
            }

            instruction = """
            Analyze the data and return each point as one line, make the answer concise and understandable: 
            1) Intensity: State the value with units (dB). Mention if it is loud enough for clear communication and note if no change is needed.
            2) Words Per Minute: State the value with units (words/minute). Indicate if the speech rate is slow and suggest a target range for improvement (120-150 words per minute).
            3) Pitch: State the value with units (Hz). Comment on whether it falls within the typical range for male or female voices. Mention if it is comfortable for listeners and note if no change is needed.
            4) Pauses Analysis: Include Short Pauses: State the value with units (pauses per minute), mention if the frequency is high and could indicate hesitation. Include Medium Pauses: State the value, mention if it is at a normal level and contributes to good rhythm. Include Long Pauses: State the value, mention if no long pauses were detected, which is good for maintaining flow. Provide an overall pause analysis, highlighting the impact of frequent short pauses on speech fluency and suggesting a reduction for smoother delivery.
            5) Summary: Highlight strengths in intensity, pitch, and medium/long pauses usage. Mention areas for improvement, including increasing speech rate and reducing short pauses for a smoother, more confident delivery. Include actionable tips for improving overall speech quality and listener engagement.
            """
            response = get_openai_response(
                model="gpt-3.5-turbo",
                system_message="You are an expert in audio evaluation for interview.",
                user_messages=[{"role": "user", "content": str(evaluation_result) + instruction}],
                max_tokens=200
            )

            return {
                "evaluation_result": evaluation_result,
                "summary": response
            }
        except Exception as e:
            print(f"Error analyzing acoustic features: {e}")
            return {"error": str(e)}

    def _analyze_content(self, transcript):
        """
        Analyze the content of a transcript using OpenAI GPT-3.5 for evaluation.
        """
        prompt = f"""
        As an expert evaluator, assess the following transcript in detail:
        Candidate's Response: "{transcript}"
        Provide:
        1. A score between 0 and 10 for clarity and relevance.
        2. Detailed feedback explaining strengths and areas of improvement.
        Format:
        Score: [score]
        Feedback: [feedback]
        """
        try:
            response = get_openai_response(
                model="gpt-3.5-turbo",
                system_message="You are an expert evaluator.",
                user_messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )

            # Extract score and feedback
            score_match = re.search(r"Score:\s*(\d+)", response)
            score = int(score_match.group(1)) if score_match else 0

            feedback_match = re.search(r"Feedback:\s*(.*)", response)
            feedback = feedback_match.group(1) if feedback_match else "No feedback provided."

            return {
                "score": score,
                "feedback": feedback
            }

        except Exception as e:
            return {
                "score": 0,
                "feedback": f"Error evaluating content: {str(e)}"
            }
