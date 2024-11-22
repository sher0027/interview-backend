import json
from myproject.utils.format import convert_floats_to_decimals, download_s3_file, parse_gpt_response, parse_s3_url
from myproject.utils.openai import get_openai_response
import soundfile as sf
import librosa
from io import BytesIO
from django.http import JsonResponse
from myproject.utils.analysis import intensity_calculation, pause_per_minute_calculation, pitch_calculation, speech_rate_calculation
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
            questions = []
            answers = []

            for index, record in enumerate(records):
                seq = record.get("seq")
                print(f"Start evaluation for sequence: {seq}")

                if seq == 1:
                    question = "Hello! How can I help you today?"
                else:
                    question = records[index - 1].get("reply", "No question available")

                transcript = record.get("transcript", "No answer available")

                self.eval_repo.save_question_answer(eid, seq, question, transcript)

                questions.append(question)
                answers.append(transcript)

                s3_url = record.get("s3_url")
                if s3_url:
                    acoustic_result = self._analyze_acoustic(s3_url)
                    self.eval_repo.save_acoustic_evaluation(eid, seq, acoustic_result)
                    acoustic_results.append(acoustic_result)  
            
                if transcript and transcript != "No reply available":
                    content_result = self._analyze_content(transcript)
                    self.eval_repo.save_content_evaluation(eid, seq, content_result)

            acoustic_summary = self._generate_acoustic_summary(acoustic_results)
            content_summary = self._generate_content_summary(questions, answers)

            self.eval_repo.save_acoustic_evaluation(eid, seq=0, acoustic=acoustic_summary)
            self.eval_repo.save_content_evaluation(eid, seq=0, content=content_summary)

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
            speech_rate = speech_rate_calculation(audio_array, sample_rate)
            pitch = pitch_calculation(audio_array)
            pauses = pause_per_minute_calculation(audio_array, sample_rate, audio_duration_minutes)

            evaluation_result = {
                "intensity": intensity,
                "speech_rate": speech_rate,
                "pitch": pitch,
                "pauses": pauses
            }

            return {
            "evaluation_result": evaluation_result
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
        Provide your response in the following JSON format:
        {{
            "score": [score between 0 and 10 for clarity and relevance],
            "feedback": "[Detailed feedback explaining strengths and areas of improvement]"
        }}
        """
        try:
            response = get_openai_response(
                model="gpt-3.5-turbo",
                system_message="You are an expert evaluator.",
                user_messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )

            evaluation_result = json.loads(response)
            score = evaluation_result.get("score", 0)
            feedback = evaluation_result.get("feedback", "No feedback provided.")

            return {
                "score": score,
                "feedback": feedback
            }


        except Exception as e:
            print(f"Error analyzing content features: {e}")
            return {"error": str(e)}

    def _generate_acoustic_summary(self, acoustic_results):
        """
        Generate a comprehensive summary and dimension analysis for acoustic analysis.
        """
        try:
            gpt_input = {
                "acoustic_results": acoustic_results,
                "instructions": (
                    "Analyze the following acoustic data and provide the following:\n"
                    "1. A comprehensive score (0-10).\n"
                    "2. Dimension-specific analysis for 'Loudness Consistency', 'Speech Rate' 'Pitch Range', "
                    "'Pause Distribution', each with a score (0-10) and feedback.\n"
                    "3. A detailed summary with actionable recommendations."
                )
            }

            prompt = f"""
            As an expert in acoustic analysis, evaluate the following data:
            Data: {gpt_input["acoustic_results"]}
            
            Instructions: {gpt_input["instructions"]}

            Respond in JSON format:
            {{
                "comprehensive_score": [score between 0 and 10],
                "dimensions": {{
                    "Loudness Consistency": {{
                        "score": [score],
                        "feedback": "[feedback]"
                    }},
                    "Pitch Range": {{
                        "score": [score],
                        "feedback": "[feedback]"
                    }},
                    "Pause Distribution": {{
                        "score": [score],
                        "feedback": "[feedback]"
                    }}
                }},
                "summary": "[summary]"
            }}
            """

            response = get_openai_response(
                model="gpt-3.5-turbo",
                system_message="You are an expert in acoustic evaluation.",
                user_messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )

            evaluation_result = parse_gpt_response(response) 
            return convert_floats_to_decimals(evaluation_result)
        except Exception as e:
            print(f"Error generating acoustic summary: {e}")
            return {"error": str(e)}


    def _generate_content_summary(self, questions, answers):
        """
        Generate a comprehensive summary and score for content analysis.
        """
        try:
            gpt_input = {
                "questions_and_answers": [{"question": q, "answer": a} for q, a in zip(questions, answers)],
                "instructions": (
                    "Evaluate the following Q&A pairs and provide the following:\n"
                    "1. Dimension-specific analysis for 'Communication Skills', 'Technical Expertise', "
                    "'Problem-solving Abilities', and 'Overall Performance', each with a score (0-10) and feedback.\n"
                    "2. A comprehensive score (0-10).\n"
                    "3. A detailed summary with actionable recommendations."
                )
            }

            prompt = f"""
            As an expert evaluator, evaluate the following data:
            Data: {gpt_input["questions_and_answers"]}
            
            Instructions: {gpt_input["instructions"]}

            Respond in JSON format:
            {{
                "scores_by_aspect": {{
                    "Communication Skills": {{
                        "score": [score],
                        "feedback": "[feedback]"
                    }},
                    "Technical Expertise": {{
                        "score": [score],
                        "feedback": "[feedback]"
                    }},
                    "Problem-solving Abilities": {{
                        "score": [score],
                        "feedback": "[feedback]"
                    }},
                    "Overall Performance": {{
                        "score": [score],
                        "feedback": "[feedback]"
                    }}
                }},
                "comprehensive_score": [score],
                "summary": "[summary]"
            }}
            """

            response = get_openai_response(
                model="gpt-3.5-turbo",
                system_message="You are an expert interview evaluator.",
                user_messages=[{"role": "user", "content": prompt}],
                max_tokens=700
            )

            evaluation_result = parse_gpt_response(response)

            return convert_floats_to_decimals(evaluation_result)
        except Exception as e:
            print(f"Error generating content summary: {e}")
            return {"error": str(e)}
