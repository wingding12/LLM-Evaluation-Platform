import os
from dotenv import load_dotenv
from openai import OpenAI
from google.generativeai import configure, GenerativeModel
import requests
from typing import Callable, Dict
import difflib
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
from together import Together

# Download required NLTK data
try:
    nltk.download('punkt')
    nltk.download('stopwords')
except:
    pass  # Handle offline cases or when already downloaded

# Load environment variables
load_dotenv(dotenv_path='.env')

# Configure API clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
configure(api_key=os.getenv('GOOGLE_API_KEY'))

def call_gemini(prompt: str) -> str:
    try:
        model = GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error calling Gemini: {str(e)}"

def call_mistral(prompt: str) -> str:
    try:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistral-medium",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Error calling Mistral: {str(e)}"

def call_llama(prompt: str) -> str:
    client = Together()

    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return(response.choices[0].message.content)

def calculate_factuality(response: str, expected: str) -> Dict[str, float]:
    """
    Calculate factuality metrics based on accuracy and relevancy.
    Returns a dictionary containing accuracy, relevancy, and overall factuality scores.
    """
    try:
        # Preprocess texts
        response = response.lower().strip()
        expected = expected.lower().strip()

        # Calculate accuracy using sequence matcher
        accuracy = difflib.SequenceMatcher(None, response, expected).ratio()

        # Calculate relevancy using word overlap
        response_words = set(word_tokenize(response)) - set(stopwords.words('english'))
        expected_words = set(word_tokenize(expected)) - set(stopwords.words('english'))
        
        if len(expected_words) > 0:
            relevancy = len(response_words.intersection(expected_words)) / len(expected_words)
        else:
            relevancy = 0.0

        # Calculate overall factuality score
        factuality = (accuracy + relevancy) / 2

        return {
            'accuracy': round(accuracy * 100, 2),
            'relevancy': round(relevancy * 100, 2),
            'factuality': round(factuality * 100, 2)
        }
    except Exception as e:
        print(f"Error calculating factuality: {str(e)}")
        return {
            'accuracy': 0.0,
            'relevancy': 0.0,
            'factuality': 0.0
        }

def evaluate_response(model_func: Callable, prompt: str, expected_output: str) -> Dict:
    """
    Wrapper function to evaluate model response and calculate factuality.
    """
    try:
        # Get model response using existing function
        response = model_func(prompt)
        
        # Calculate factuality metrics
        metrics = calculate_factuality(response, expected_output)
        
        return {
            'response': response,
            'metrics': metrics
        }
    except Exception as e:
        return {
            'response': f"Error: {str(e)}",
            'metrics': {
                'accuracy': 0.0,
                'relevancy': 0.0,
                'factuality': 0.0
            }
        }

def model_functions(model_name: str) -> Callable[[str, str], Dict]:
    """
    Updated model_functions to return a function that handles both response generation and evaluation.
    """
    base_model_map = {
        "Gemini": call_gemini,
        "Mistral": call_mistral,
        "Llama": call_llama
    }
    
    model_func = base_model_map.get(model_name)
    if not model_func:
        return lambda prompt, expected: {
            'response': f"Model {model_name} not implemented",
            'metrics': {'accuracy': 0.0, 'relevancy': 0.0, 'factuality': 0.0}
        }
    
    return lambda prompt, expected: evaluate_response(model_func, prompt, expected) 